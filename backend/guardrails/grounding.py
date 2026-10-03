import re
from typing import List, Dict, Any, Tuple


class GroundingValidator:
    """
    Validates that the generated response is strictly grounded in the retrieved context
    and calculates a groundedness score [0.0 - 1.0].
    """

    @staticmethod
    def evaluate_grounding(answer: str, context: str) -> Tuple[float, bool]:
        if not answer or not context:
            return 0.0, False

        # Tokenize answer key terms (words with len >= 3)
        answer_words = re.findall(r"\b[a-zA-Z0-9_\-\$]{3,}\b", answer.lower())
        context_lower = context.lower()

        if not answer_words:
            return 1.0, True

        supported_count = sum(1 for w in answer_words if w in context_lower)
        grounding_score = supported_count / len(answer_words)

        # Check for insufficient information standard response
        if "couldn't find sufficient information" in answer.lower() or "don't have access" in answer.lower():
            return 1.0, True

        is_grounded = grounding_score >= 0.55
        return round(grounding_score, 3), is_grounded
