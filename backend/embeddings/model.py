import logging
from typing import List, Union
import numpy as np
from backend.config.settings import settings

logger = logging.getLogger(__name__)

_model_instance = None


def get_embedding_model():
    """Singleton getter for the sentence transformers embedding model."""
    global _model_instance
    if _model_instance is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL} on {settings.EMBEDDING_DEVICE}")
            _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE)
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            raise e
    return _model_instance
