from typing import List, Union
import numpy as np
from backend.embeddings.model import get_embedding_model
from backend.embeddings.cache import embedding_cache
from backend.config.settings import settings


class EmbeddingGenerator:
    """Generates L2-normalized embeddings for chunks and queries."""

    @staticmethod
    def generate_embeddings(texts: List[str], use_cache: bool = True) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        model = get_embedding_model()
        uncached_indices = []
        uncached_texts = []
        results = [None] * len(texts)

        if use_cache:
            for idx, text in enumerate(texts):
                cached_vec = embedding_cache.get(text, settings.EMBEDDING_MODEL)
                if cached_vec is not None:
                    results[idx] = cached_vec
                else:
                    uncached_indices.append(idx)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts

        if uncached_texts:
            embeddings = model.encode(
                uncached_texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            embeddings = np.array(embeddings, dtype=np.float32)
            for idx, raw_idx in enumerate(uncached_indices):
                vec = embeddings[idx]
                results[raw_idx] = vec
                if use_cache:
                    embedding_cache.set(uncached_texts[idx], settings.EMBEDDING_MODEL, vec)

        return np.array(results, dtype=np.float32)

    @staticmethod
    def generate_query_embedding(query: str) -> np.ndarray:
        """Generate embedding for a single user query."""
        vecs = EmbeddingGenerator.generate_embeddings([query], use_cache=True)
        return vecs[0]
