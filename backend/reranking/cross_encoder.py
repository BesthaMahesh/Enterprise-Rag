import logging
from typing import List, Tuple, Dict, Any
from backend.config.settings import settings

logger = logging.getLogger(__name__)

_reranker_instance = None


def get_cross_encoder():
    """Singleton getter for CrossEncoder reranker model."""
    global _reranker_instance
    if _reranker_instance is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading CrossEncoder reranker: {settings.RERANKER_MODEL} on {settings.RERANKER_DEVICE}")
            _reranker_instance = CrossEncoder(settings.RERANKER_MODEL, device=settings.RERANKER_DEVICE)
        except Exception as e:
            logger.warning(f"Could not load CrossEncoder model ({e}). Using cosine/RRF fallback scorer.")
            _reranker_instance = None
    return _reranker_instance
