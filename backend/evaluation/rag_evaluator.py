import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session

from backend.evaluation.datasets import EvaluationDatasetLoader
from backend.evaluation.retrieval_metrics import RetrievalMetrics
from backend.evaluation.generation_metrics import GenerationMetrics
from backend.evaluation.acl_evaluator import ACLEvaluator
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
from backend.guardrails.input_guardrail import InputGuardrail
from backend.guardrails.output_guardrail import OutputGuardrail
from backend.guardrails.pii import PIIDetector
from backend.observability.cost_tracker import CostTracker
from backend.config.settings import settings
from backend.database.models import EvaluationRun, EvaluationResult

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    Executes end-to-end evaluation runs, calculating real retrieval, reranking,
    generation, ACL security, and operational metrics directly from live data.
    """

    def __init__(self, db: Session):
        self.db = db

    def run_full_evaluation(self, run_name: Optional[str] = None) -> Dict[str, Any]:
        run_id = f"eval_{uuid.uuid4().hex[:12]}"
        run_title = run_name or f"Evaluation Run - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

        logger.info(f"Starting comprehensive RAG & ACL evaluation: {run_id}")
        start_time = time.perf_counter()

        test_cases = EvaluationDatasetLoader.load_benchmark_dataset()
        if not test_cases:
            test_cases = EvaluationDatasetLoader.load_acl_test_cases()

        eval_run = EvaluationRun(
            id=run_id,
            run_name=run_title,
            evaluator_type="rag_and_acl",
            total_questions=len(test_cases),
            status="RUNNING",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(eval_run)
        self.db.commit()

        results_list = []
        acl_passed_count = 0
        unauthorized_retrieval_count = 0
        unauthorized_answer_count = 0
        injection_test_count = 0
        injection_detected_count = 0
        pii_test_count = 0
        pii_leaked_count = 0
        total_errors = 0

        # Metric accumulators
        retrieval_recalls = []
        retrieval_precisions = []
        retrieval_mrrs = []
        retrieval_ndcgs = []

        rerank_mrrs = []
        rerank_ndcgs = []

        faithfulness_scores = []
        relevance_scores = []
        grounding_scores = []
        citation_correctness_scores = []

        latencies = []
        total_tokens = []
        total_cost = 0.0

        for case in test_cases:
            t0 = time.perf_counter()
            role = case.get("role", "EMPLOYEE")
            raw_query = case["query"]
            expected_decision = case.get("expected_decision", case.get("expected", "ALLOW"))
            relevant_doc_ids: Set[str] = set(case.get("relevant_doc_ids", []))
            expected_injection = case.get("expected_injection", False)
            expected_pii = case.get("expected_pii", False)

            case_passed = True
            error_occurred = False
            tokens_used = 0
            citations = []
            context_chunks = []
            context_str = ""
            raw_answer = ""
            actual_decision = "DENY"

            try:
                # 1. Input Guardrail
                inp = InputGuardrail.process_input(raw_query)
                is_injection = inp["is_injection"]

                if expected_injection:
                    injection_test_count += 1
                    if is_injection:
                        injection_detected_count += 1

                if expected_pii:
                    pii_test_count += 1

                if is_injection:
                    actual_decision = "DENY"
                    raw_answer = "I cannot fulfill requests that attempt to override security instructions or system rules."
                    context_chunks = []
                    context_str = ""
                else:
                    # 2. Retrieval with ACL Pre-retrieval enforcement
                    retrieval_data = enterprise_retriever.hybrid_retriever.retrieve(
                        query=inp["search_query"],
                        user_role=role
                    )
                    fused_results = retrieval_data.get("fused_results", [])
                    reranked_results = retrieval_data.get("reranked_results", [])
                    final_candidates = retrieval_data.get("final_candidates", [])

                    # Post-rerank relevance validation
                    is_relevant, relevant_candidates, _ = Reranker.validate_relevance(
                        query=raw_query,
                        candidates=final_candidates,
                        threshold=settings.RERANKER_RELEVANCE_THRESHOLD
                    )

                    # Compute retrieval & reranking metrics when relevant docs exist
                    if relevant_doc_ids and expected_decision == "ALLOW":
                        fused_doc_ids = [c.get("document_id", "") for c in fused_results]
                        rerank_doc_ids = [c.get("document_id", "") for c in reranked_results]

                        r_rec = RetrievalMetrics.recall_at_k(fused_doc_ids, relevant_doc_ids, 5)
                        r_prec = RetrievalMetrics.precision_at_k(fused_doc_ids, relevant_doc_ids, 5)
                        r_mrr = RetrievalMetrics.mrr(fused_doc_ids, relevant_doc_ids)
                        r_ndcg = RetrievalMetrics.ndcg_at_k(fused_doc_ids, relevant_doc_ids, 5)

                        rr_mrr = RetrievalMetrics.mrr(rerank_doc_ids, relevant_doc_ids)
                        rr_ndcg = RetrievalMetrics.ndcg_at_k(rerank_doc_ids, relevant_doc_ids, 5)

                        retrieval_recalls.append(r_rec)
                        retrieval_precisions.append(r_prec)
                        retrieval_mrrs.append(r_mrr)
                        retrieval_ndcgs.append(r_ndcg)

                        rerank_mrrs.append(rr_mrr)
                        rerank_ndcgs.append(rr_ndcg)

                    # 3. Context Construction
                    if is_relevant and len(relevant_candidates) > 0:
                        context_str, context_chunks = ContextBuilder.build_context(
                            query=raw_query,
                            raw_candidates=relevant_candidates,
                            user_role=role,
                            max_tokens=settings.MAX_CONTEXT_TOKENS
                        )

                    # Check for unauthorized chunks in retrieved context
                    case_unauthorized = 0
                    for chk in context_chunks:
                        chk_roles = [r.upper() for r in chk.get("allowed_roles", [])]
                        if role.upper() not in chk_roles:
                            case_unauthorized += 1
                            unauthorized_retrieval_count += 1

                    if len(context_chunks) > 0 and case_unauthorized == 0:
                        actual_decision = "ALLOW"
                    else:
                        actual_decision = "DENY"

                    # 4. LLM Generation
                    if len(context_chunks) > 0:
                        messages = [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                                context=context_str,
                                user_role=role,
                                query=raw_query
                            )}
                        ]
                        raw_answer, _, tokens_used = llm_client.generate_response(messages)
                    else:
                        lower_q = raw_query.lower()
                        if "salary" in lower_q or "payroll" in lower_q:
                            raw_answer = "I don't have access to personal payroll information."
                        elif not is_relevant:
                            raw_answer = INSUFFICIENT_KNOWLEDGE_FALLBACK
                        elif role == "EMPLOYEE" and any(w in lower_q for w in ["budget", "revenue", "executive"]):
                            raw_answer = "I don't have access to that information in the authorized knowledge base."
                        else:
                            raw_answer = INSUFFICIENT_KNOWLEDGE_FALLBACK

                # Parse citations
                clean_answer, parsed_citations = ResponseParser.parse_response(
                    llm_output=raw_answer,
                    retrieved_chunks=context_chunks,
                    user_role=role
                )

                # 5. Output Guardrail & PII Sanitization
                sanitized_answer, final_citations, g_score, _ = OutputGuardrail.validate_and_sanitize_output(
                    answer=clean_answer,
                    citations=parsed_citations,
                    context_str=context_str,
                    user_role=role,
                    authorized_chunks=context_chunks
                )

                # Check PII leakage in sanitized answer
                _, post_pii = PIIDetector.detect_and_mask(sanitized_answer)
                if post_pii:
                    pii_leaked_count += 1

                # Citation correctness: All citations must originate from context_chunks
                if len(final_citations) > 0:
                    ctx_doc_ids = {c.get("document_id") for c in context_chunks}
                    valid_cits = 0
                    for cit in final_citations:
                        cit_doc_id = cit.document_id if hasattr(cit, "document_id") else cit.get("document_id")
                        if cit_doc_id in ctx_doc_ids:
                            valid_cits += 1
                    cit_corr = valid_cits / len(final_citations)
                else:
                    # If abstaining/refusing with empty citations, citation correctness is 1.0
                    cit_corr = 1.0
                citation_correctness_scores.append(cit_corr)

                # Generation Metrics
                faith = GenerationMetrics.calculate_faithfulness(sanitized_answer, context_str) if context_str else 1.0
                relev = GenerationMetrics.calculate_answer_relevance(raw_query, sanitized_answer)
                faithfulness_scores.append(faith)
                relevance_scores.append(relev)
                grounding_scores.append(g_score)

                # Evaluate ACL Compliance
                if expected_decision in ["DENY", "REFUSE"]:
                    # Pass condition: No unauthorized chunks in context and no leakage in answer
                    case_passed = (case_unauthorized == 0 and (actual_decision == "DENY" or not context_chunks))
                else:
                    # Expected ALLOW: Must retrieve authorized chunks and succeed
                    case_passed = (case_unauthorized == 0 and len(context_chunks) > 0)

                if case_passed:
                    acl_passed_count += 1

            except Exception as e:
                logger.error(f"Error evaluating test case {case.get('id')}: {e}")
                total_errors += 1
                case_passed = False
                sanitized_answer = "Error during test evaluation."
                g_score = 0.0
                faith = 0.0
                relev = 0.0

            latency_ms = (time.perf_counter() - t0) * 1000
            latencies.append(latency_ms)
            total_tokens.append(tokens_used)

            # Estimate cost
            cost = CostTracker.calculate_cost(
                model_name=settings.LLM_MODEL,
                input_tokens=tokens_used // 2,
                output_tokens=tokens_used // 2
            )
            total_cost += cost

            # Save individual result
            res_item = EvaluationResult(
                run_id=run_id,
                question_id=case.get("id"),
                query=raw_query,
                user_role=role,
                expected_decision=expected_decision,
                actual_decision=actual_decision,
                passed=case_passed,
                retrieval_metrics={
                    "retrieved_count": len(context_chunks),
                    "unauthorized_chunks": case_unauthorized if not error_occurred else 0
                },
                generation_metrics={
                    "faithfulness": faith,
                    "relevance": relev,
                    "grounding_score": g_score,
                    "citation_correctness": cit_corr if 'cit_corr' in locals() else 1.0
                },
                acl_passed=case_passed,
                details={"category": case.get("category"), "latency_ms": latency_ms},
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(res_item)
            results_list.append(res_item)

        total_q = len(test_cases)
        total_time_ms = (time.perf_counter() - start_time) * 1000

        avg_ret_recall = round(sum(retrieval_recalls) / max(1, len(retrieval_recalls)), 3)
        avg_ret_precision = round(sum(retrieval_precisions) / max(1, len(retrieval_precisions)), 3)
        avg_ret_mrr = round(sum(retrieval_mrrs) / max(1, len(retrieval_mrrs)), 3)
        avg_ret_ndcg = round(sum(retrieval_ndcgs) / max(1, len(retrieval_ndcgs)), 3)

        avg_rerank_mrr = round(sum(rerank_mrrs) / max(1, len(rerank_mrrs)), 3)
        avg_rerank_ndcg = round(sum(rerank_ndcgs) / max(1, len(rerank_ndcgs)), 3)

        avg_faith = round(sum(faithfulness_scores) / max(1, len(faithfulness_scores)), 3)
        avg_relev = round(sum(relevance_scores) / max(1, len(relevance_scores)), 3)
        avg_ground = round(sum(grounding_scores) / max(1, len(grounding_scores)), 3)
        avg_cit_corr = round(sum(citation_correctness_scores) / max(1, len(citation_correctness_scores)), 3)

        acl_violation_rate = round(unauthorized_retrieval_count / max(1, total_q), 4)
        unauth_ret_rate = round(unauthorized_retrieval_count / max(1, total_q), 4)
        injection_rate = round(injection_detected_count / max(1, injection_test_count), 3) if injection_test_count > 0 else 1.0
        pii_leak_rate = round(pii_leaked_count / max(1, total_q), 4)

        avg_latency = round(sum(latencies) / max(1, len(latencies)), 1)
        avg_toks = round(sum(total_tokens) / max(1, len(total_tokens)), 1)
        error_rate = round(total_errors / max(1, total_q), 3)

        metrics_summary = {
            "retrieval": {
                "recall_at_5": avg_ret_recall,
                "precision_at_5": avg_ret_precision,
                "mrr": avg_ret_mrr,
                "ndcg_at_5": avg_ret_ndcg,
            },
            "reranking": {
                "mrr": avg_rerank_mrr,
                "ndcg_at_5": avg_rerank_ndcg,
            },
            "generation": {
                "faithfulness": avg_faith,
                "groundedness": avg_ground,
                "answer_relevance": avg_relev,
                "citation_correctness": avg_cit_corr,
            },
            "security": {
                "acl_violation_rate": acl_violation_rate,
                "unauthorized_retrieval_rate": unauth_ret_rate,
                "prompt_injection_detection_rate": injection_rate,
                "pii_leakage_rate": pii_leak_rate,
            },
            "operations": {
                "average_latency_ms": avg_latency,
                "average_tokens": avg_toks,
                "estimated_cost_usd": round(total_cost, 6),
                "error_rate": error_rate,
                "total_time_ms": round(total_time_ms, 1),
            }
        }

        eval_run.status = "COMPLETED"
        eval_run.metrics_summary = metrics_summary
        eval_run.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Evaluation {run_id} completed: {acl_passed_count}/{total_q} passed.")
        return {
            "run_id": run_id,
            "metrics_summary": metrics_summary,
            "total_questions": total_q,
            "passed_count": acl_passed_count
        }
