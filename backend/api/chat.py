import re
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import User, Conversation, Message
from backend.auth.dependencies import get_current_user
from backend.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceCitation,
    RetrievalDebugMetrics,
    ConversationResponse,
    MessageResponse
)
from backend.guardrails.input_guardrail import InputGuardrail
from backend.guardrails.output_guardrail import OutputGuardrail
from backend.guardrails.pii import PIIDetector
from backend.retrieval.retriever import enterprise_retriever
from backend.reranking.reranker import Reranker
from backend.context.builder import ContextBuilder
from backend.llm.client import llm_client
from backend.llm.prompts import (
    INSUFFICIENT_KNOWLEDGE_FALLBACK,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from backend.llm.response_parser import ResponseParser
from backend.observability.tracing import get_current_request_id, get_current_trace_id
from backend.observability.cost_tracker import CostTracker
from backend.observability.audit import AuditLogger
from backend.reliability.rate_limiter import rate_limiter
from backend.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat & Conversations"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.perf_counter()
    req_id = get_current_request_id()
    trc_id = get_current_trace_id()

    # Rate limiting
    allowed, remaining = rate_limiter.is_allowed(current_user.email)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a minute before making more requests."
        )

    # 1. Input Processing & Guardrails
    input_result = InputGuardrail.process_input(req.query)
    raw_query = req.query
    search_query = input_result["search_query"]
    query_class = input_result["query_class"]
    is_injection = input_result["is_injection"]
    is_greeting = input_result.get("is_greeting", False)

    dense_res = []
    sparse_res = []
    fused_res = []
    reranked_res = []
    final_candidates = []
    authorized_context_chunks = []
    context_str = ""
    retrieval_latency_ms = 0.0
    llm_latency_ms = 0.0
    llm_tokens = 0

    if is_injection:
        AuditLogger.log_event(
            db=db,
            user_email=current_user.email,
            role=current_user.role,
            action="PROMPT_INJECTION_DETECTED",
            resource="Chat",
            query=PIIDetector.sanitize_for_logging(raw_query),
            acl_decision="DENIED",
            reason=input_result["injection_reason"],
            request_id=req_id,
            trace_id=trc_id
        )
        raw_llm_answer = "I cannot fulfill requests that attempt to override security instructions or system rules."
    elif is_greeting:
        raw_llm_answer = (
            "Hello! I am your Enterprise AI Assistant. How can I help you today? "
            "You can ask me questions about workplace policies, leave requests, employee benefits, "
            "travel reimbursements, code of conduct, and more."
        )
    else:
        # 2. Retrieval with Strict ACL Pre-filtering
        t_retrieval_start = time.perf_counter()
        retrieval_data = enterprise_retriever.retrieve_authorized_context(
            query=search_query,
            user_role=current_user.role
        )
        retrieval_latency_ms = (time.perf_counter() - t_retrieval_start) * 1000

        dense_res = retrieval_data.get("dense_results", [])
        sparse_res = retrieval_data.get("sparse_results", [])
        fused_res = retrieval_data.get("fused_results", [])
        reranked_res = retrieval_data.get("reranked_results", [])
        final_candidates = retrieval_data.get("final_candidates", [])

        # Post-reranking relevance validation & abstention
        is_relevant, relevant_candidates, top_rerank_score = Reranker.validate_relevance(
            query=raw_query,
            candidates=final_candidates,
            threshold=settings.RERANKER_RELEVANCE_THRESHOLD
        )

        if not is_relevant:
            logger.info(
                f"Query relevance validation abstained: top score {top_rerank_score:.3f} < threshold {settings.RERANKER_RELEVANCE_THRESHOLD:.3f}"
            )
            raw_llm_answer = INSUFFICIENT_KNOWLEDGE_FALLBACK
        else:
            # 3. Context Construction
            context_str, authorized_context_chunks = ContextBuilder.build_context(
                query=raw_query,
                raw_candidates=relevant_candidates,
                user_role=current_user.role,
                max_tokens=settings.MAX_CONTEXT_TOKENS
            )

            # 4. LLM Generation
            t_llm_start = time.perf_counter()
            if len(authorized_context_chunks) > 0:
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                        context=context_str,
                        user_role=current_user.role,
                        query=raw_query
                    )}
                ]
                try:
                    raw_llm_answer, llm_latency_ms, llm_tokens = llm_client.generate_response(messages)
                except Exception as e:
                    logger.error(f"LLM generation failed [req={req_id}, trace={trc_id}]: {e}")
                    raw_llm_answer = "AI service is temporarily unavailable. Please try again."
                    authorized_context_chunks = []
            else:
                llm_latency_ms = 0.0
                lower_q = raw_query.lower()
                if "salary" in lower_q or "payroll" in lower_q or "compensation" in lower_q or "my pay" in lower_q:
                    raw_llm_answer = "I don't have access to your personal payroll information through this assistant."
                elif current_user.role == "EMPLOYEE" and query_class in ["FINANCE", "RESTRICTED", "HR"]:
                    raw_llm_answer = "I'm sorry, I don't have access to that information."
                else:
                    raw_llm_answer = INSUFFICIENT_KNOWLEDGE_FALLBACK

    # Parse Citations (Single source-of-truth from authorized context)
    raw_answer, initial_citations = ResponseParser.parse_response(
        llm_output=raw_llm_answer,
        retrieved_chunks=authorized_context_chunks,
        user_role=current_user.role
    )

    # 5. Output Guardrail & Validation
    sanitized_answer, final_citations, grounding_score, guardrail_decision = OutputGuardrail.validate_and_sanitize_output(
        answer=raw_answer,
        citations=initial_citations,
        context_str=context_str,
        user_role=current_user.role,
        authorized_chunks=authorized_context_chunks
    )

    total_latency_ms = (time.perf_counter() - start_time) * 1000

    # ACL decision outcome
    if is_injection:
        acl_decision = "DENIED"
        guardrail_decision = "BLOCKED"
    else:
        acl_decision = "ALLOWED" if len(authorized_context_chunks) > 0 else "DENIED"

    # Cost Tracking
    context_tokens = len(context_str.split()) * 4 // 3
    estimated_cost = CostTracker.calculate_cost(settings.LLM_MODEL, context_tokens, llm_tokens)

    # Conversation & Message Persistence
    def generate_conversation_title(query: str) -> str:
        q = query.strip()
        cleaned = re.sub(
            r"^(?:what\s+(?:is|are)\s+(?:the\s+)?|how\s+(?:do\s+I|to|can\s+I)\s+|can\s+I\s+|tell\s+me\s+about\s+(?:the\s+)?|explain\s+(?:the\s+)?)",
            "",
            q,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(r"[\?\.\!]+$", "", cleaned).strip()
        if not cleaned:
            cleaned = q[:40]
        words = cleaned.split()
        if len(words) > 5:
            cleaned = " ".join(words[:5])
        return cleaned[:45].title()

    conv_id = req.conversation_id
    if not conv_id:
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        new_conv = Conversation(
            id=conv_id,
            user_id=current_user.id,
            title=generate_conversation_title(raw_query),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_conv)
        db.commit()
    else:
        # Check ownership
        conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == current_user.id).first()
        if not conv:
            conv_id = f"conv_{uuid.uuid4().hex[:12]}"
            new_conv = Conversation(
                id=conv_id,
                user_id=current_user.id,
                title=generate_conversation_title(raw_query),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(new_conv)
            db.commit()
        else:
            conv.updated_at = datetime.now(timezone.utc)

    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    user_msg_id = f"msg_{uuid.uuid4().hex[:12]}"

    # Save user message
    user_msg = Message(
        id=user_msg_id,
        conversation_id=conv_id,
        role="user",
        content=PIIDetector.sanitize_for_logging(raw_query),
        tokens=len(raw_query.split()),
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_msg)

    # Metrics object
    debug_metrics = RetrievalDebugMetrics(
        dense_count=len(dense_res),
        sparse_count=len(sparse_res),
        rrf_fused_count=len(fused_res),
        reranked_count=len(reranked_res),
        authorized_document_count=len(authorized_context_chunks),
        context_tokens=context_tokens,
        retrieval_latency_ms=round(retrieval_latency_ms, 2),
        llm_latency_ms=round(llm_latency_ms, 2),
        total_latency_ms=round(total_latency_ms, 2),
        estimated_cost_usd=estimated_cost,
        grounding_score=grounding_score,
        acl_decision=acl_decision,
        guardrail_decision=guardrail_decision,
        query_classification=query_class
    )

    # Save assistant message
    asst_msg = Message(
        id=msg_id,
        conversation_id=conv_id,
        role="assistant",
        content=sanitized_answer,
        sources=[c.model_dump() for c in final_citations],
        metrics=debug_metrics.model_dump(),
        tokens=llm_tokens,
        created_at=datetime.now(timezone.utc)
    )
    db.add(asst_msg)
    db.commit()

    # 6. Audit Logging
    AuditLogger.log_event(
        db=db,
        user_email=current_user.email,
        role=current_user.role,
        action="QUERY_SEARCH",
        resource=f"Conversation:{conv_id}",
        query=PIIDetector.sanitize_for_logging(raw_query),
        acl_decision=acl_decision,
        reason="Authorized search executed" if acl_decision == "ALLOWED" else "No authorized documents matched query",
        latency_ms=total_latency_ms,
        request_id=req_id,
        trace_id=trc_id,
        metadata_json={
            "query_class": query_class,
            "grounding_score": grounding_score,
            "authorized_chunks": len(authorized_context_chunks),
            "citations_count": len(final_citations),
            "cost_usd": estimated_cost
        }
    )

    return ChatResponse(
        conversation_id=conv_id,
        message_id=msg_id,
        answer=sanitized_answer,
        sources=final_citations,
        acl_decision=acl_decision,
        grounding_score=grounding_score,
        query_class=query_class,
        metrics=debug_metrics if (req.include_debug_metrics or current_user.role in ["HR", "ADMIN", "FINANCE"]) else None,
        created_at=datetime.now(timezone.utc)
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .all()
    )
    return convs


@router.get("/conversations/{conv_id}", response_model=ConversationResponse)
def get_conversation_details(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully", "id": conv_id}


from pydantic import BaseModel

class ChatFeedbackRequest(BaseModel):
    message_id: str
    feedback: str
    conversation_id: Optional[str] = None
    comments: Optional[str] = None


@router.post("/chat/feedback")
def submit_feedback(
    req: ChatFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    AuditLogger.log_event(
        db=db,
        user_email=current_user.email,
        role=current_user.role,
        action="CHAT_FEEDBACK",
        resource=f"Message:{req.message_id}",
        query=f"Feedback: {req.feedback}",
        acl_decision="ALLOWED",
        reason="User response feedback",
        metadata_json={
            "feedback": req.feedback,
            "conversation_id": req.conversation_id,
            "comments": req.comments
        }
    )
    return {"status": "recorded", "message_id": req.message_id}
