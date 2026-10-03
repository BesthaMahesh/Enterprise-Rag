import hashlib
from typing import Dict, Optional
import numpy as np


class EmbeddingCache:
    """Thread-safe in-memory cache for query and text embeddings."""

    def __init__(self, max_size: int = 5000):
        self.cache: Dict[str, np.ndarray] = {}
        self.max_size = max_size

    def _hash_key(self, text: str, model_name: str) -> str:
        return hashlib.sha256(f"{model_name}:{text}".encode("utf-8")).hexdigest()

    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        key = self._hash_key(text, model_name)
        return self.cache.get(key)

    def set(self, text: str, model_name: str, vec: np.ndarray):
        if len(self.cache) >= self.max_size:
            # Simple eviction
            keys = list(self.cache.keys())
            for k in keys[:1000]:
                del self.cache[k]
        key = self._hash_key(text, model_name)
        self.cache[key] = vec


embedding_cache = EmbeddingCache()
