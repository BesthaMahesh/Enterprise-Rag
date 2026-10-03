import logging
from typing import Tuple, List, Dict, Any
from backend.guardrails.grounding import GroundingValidator
from backend.guardrails.citation import CitationValidator
from backend.guardrails.pii import PIIDetector
from backend.schemas.chat import SourceCitation
from backend.acl.service import acl_service

logger = logging.getLogger(__name__)


class OutputGuardrail:
    """Validates the generated output, citations, and groundedness before returning to client."""

    @staticmethod
    def validate_and_sanitize_output(
        answer: str,
        citations: List[SourceCitation],
        context_str: str,
        user_role: str,
        authorized_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[SourceCitation], float, str]:
        # 1. Evaluate Grounding
        grounding_score, is_grounded = GroundingValidator.evaluate_grounding(answer, context_str)

        # 2. Validate Citations
        _, valid_citations = CitationValidator.validate_citations(citations, authorized_chunks)

        # 3. Filter citations by role ACL (no leaking title of restricted docs)
        sanitized_citations = []
        for cit in valid_citations:
            if cit.classification == "INTERNAL" or user_role in ["HR", "ADMIN", "FINANCE"]:
                sanitized_citations.append(cit)
            elif user_role == "EMPLOYEE" and cit.classification == "INTERNAL":
                sanitized_citations.append(cit)

        # 4. Check PII in output
        sanitized_answer, pii_detected = PIIDetector.detect_and_mask(answer)

        # 5. If context was empty or insufficient and answer attempted to hallucinate
        if len(authorized_chunks) == 0:
            lower_ans = answer.lower()
            if "salary" in lower_ans or "payroll" in lower_ans:
                sanitized_answer = "I don't have access to your personal payroll information through this assistant."
            elif any(g in lower_ans for g in ["hello", "how can i help", "how can i assist", "cannot fulfill", "security instructions"]):
                sanitized_answer = answer
            elif "couldn't find" in lower_ans or "insufficient" in lower_ans:
                sanitized_answer = answer
            elif user_role == "EMPLOYEE" and any(w in lower_ans for w in ["budget", "revenue", "restricted", "confidential"]):
                sanitized_answer = "I'm sorry, I don't have access to that information."
            else:
                sanitized_answer = answer if answer else "I couldn't find enough information in the available knowledge to answer that accurately."
            sanitized_citations = []
            return sanitized_answer, sanitized_citations, 1.0, "PASSED"

        # 6. Fallback if hallucinated with very low score and no refusal
        if not is_grounded and grounding_score < 0.25 and "couldn't find" not in sanitized_answer.lower():
            logger.warning(f"Output failed groundedness check (score={grounding_score}). Returning controlled fallback.")
            sanitized_answer = "I couldn't find enough information in the available knowledge to answer that accurately."

        # 7. Context/Citation Consistency: If the response is an abstention or security refusal,
        # never display sources claiming the refusal is based on those documents.
        refusal_markers = [
            "couldn't find enough",
            "couldn't find sufficient",
            "don't have access to that information",
            "don't have access to your personal payroll",
            "cannot fulfill requests that attempt to override",
            "temporarily unavailable",
            "hello! i am your enterprise ai assistant",
            "how can i assist you today"
        ]
        if any(marker in sanitized_answer.lower() for marker in refusal_markers):
            sanitized_citations = []

        return sanitized_answer, sanitized_citations, grounding_score, "PASSED"
