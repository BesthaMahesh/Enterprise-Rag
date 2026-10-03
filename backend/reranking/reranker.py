import logging
from typing import List, Dict, Any, Tuple
from backend.reranking.cross_encoder import get_cross_encoder
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranks candidate chunks based on cross-encoder query-document attention scoring.
    """

    @staticmethod
    def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        reranker_model = get_cross_encoder()
        if reranker_model is not None:
            pairs = [[query, c["content"]] for c in candidates]
            try:
                scores = reranker_model.predict(pairs, show_progress_bar=False)
                for idx, score in enumerate(scores):
                    candidates[idx]["reranker_score"] = float(score)
            except Exception as e:
                logger.error(f"Error running cross-encoder: {e}")
                for c in candidates:
                    c["reranker_score"] = c.get("rrf_score", 0.0)
        else:
            # Fallback to RRF score
            for c in candidates:
                c["reranker_score"] = c.get("rrf_score", 0.0)

        # Sort by reranker_score descending
        reranked = sorted(candidates, key=lambda x: x.get("reranker_score", 0.0), reverse=True)
        return reranked[:top_k]

    @classmethod
    def validate_relevance(
        cls,
        query: str,
        candidates: List[Dict[str, Any]],
        threshold: float = None
    ) -> Tuple[bool, List[Dict[str, Any]], float]:
        """
        Validates post-reranking relevance against a configurable threshold.
        Returns: (is_relevant: bool, relevant_candidates: List[Dict], top_score: float)
        """
        thresh = threshold if threshold is not None else settings.RERANKER_RELEVANCE_THRESHOLD
        if not candidates:
            return False, [], -999.0

        top_score = candidates[0].get("reranker_score", -999.0)
        if top_score < thresh:
            logger.info(
                f"Query relevance validation abstained: top score {top_score:.3f} < threshold {thresh:.3f}"
            )
            return False, [], top_score

        # Retain candidate chunks meeting the relevance criteria
        relevant = [c for c in candidates if c.get("reranker_score", -999.0) >= thresh]
        return True, relevant, top_score
