from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    document_id: str
    document_title: str
    section: Optional[str] = "General"
    page_number: Optional[int] = None
    classification: str = "INTERNAL"
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None
    allowed_roles: List[str] = []


class RetrievalDebugMetrics(BaseModel):
    dense_count: int = 0
    sparse_count: int = 0
    rrf_fused_count: int = 0
    reranked_count: int = 0
    authorized_document_count: int = 0
    context_tokens: int = 0
    retrieval_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    grounding_score: float = 1.0
    acl_decision: str = "ALLOWED"
    guardrail_decision: str = "PASSED"
    query_classification: str = "GENERAL"


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    conversation_id: Optional[str] = None
    include_debug_metrics: Optional[bool] = False


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    sources: List[SourceCitation] = []
    acl_decision: str = "ALLOWED"
    grounding_score: float = 1.0
    query_class: str = "GENERAL"
    metrics: Optional[RetrievalDebugMetrics] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    tokens: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = []

    class Config:
        from_attributes = True
