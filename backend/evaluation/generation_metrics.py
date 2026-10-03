import re
from typing import List, Dict, Any


class GenerationMetrics:
    """Calculates generation quality metrics: Faithfulness, Answer Relevance, Groundedness."""

    @staticmethod
    def calculate_faithfulness(answer: str, context: str) -> float:
        """Percentage of answer tokens supported by context."""
        if not answer or not context:
            return 0.0
        words = re.findall(r"\b[a-zA-Z0-9_\-\$]{3,}\b", answer.lower())
        if not words:
            return 1.0
        context_lower = context.lower()
        supported = sum(1 for w in words if w in context_lower)
        return round(supported / len(words), 3)

    @staticmethod
    def calculate_answer_relevance(query: str, answer: str) -> float:
        """Overlap between question key concepts and generated answer."""
        query_words = set(re.findall(r"\b[a-zA-Z0-9_\-\$]{3,}\b", query.lower()))
        if not query_words:
            return 1.0
        answer_lower = answer.lower()
        overlap = sum(1 for w in query_words if w in answer_lower)
        return round(min(1.0, (overlap / len(query_words)) * 1.2), 3)
