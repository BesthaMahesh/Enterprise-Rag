import os
import json
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss
from backend.embeddings.generator import EmbeddingGenerator
from backend.acl.service import acl_service
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class DenseRetriever:
    """
    FAISS-based dense vector retriever with ACL filtering.
    """

    def __init__(self, index_path: str = None, metadata_path: str = None):
        self.index_path = index_path or settings.VECTOR_INDEX_PATH
        self.metadata_path = metadata_path or settings.VECTOR_METADATA_PATH
        self.index: faiss.Index = None
        self.chunks_metadata: List[Dict[str, Any]] = []
        self.load_index()

    def load_index(self):
        """Load FAISS index and companion metadata if available."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.chunks_metadata = json.load(f)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors and {len(self.chunks_metadata)} chunk metadata.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                self.index = None
                self.chunks_metadata = []

    def save_index(self, index: faiss.Index, chunks_metadata: List[Dict[str, Any]]):
        """Save FAISS index and metadata to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(index, self.index_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(chunks_metadata, f, ensure_ascii=False, indent=2)
        self.index = index
        self.chunks_metadata = chunks_metadata
        logger.info(f"Saved FAISS index with {index.ntotal} vectors.")

    def search(self, query: str, user_role: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Execute dense search strictly filtered by user role ACL.
        """
        if self.index is None or len(self.chunks_metadata) == 0:
            return []

        # Generate query vector
        query_vec = EmbeddingGenerator.generate_query_embedding(query)
        query_vec = np.expand_dims(query_vec, axis=0).astype(np.float32)

        # Retrieve a broader candidate set to ensure sufficient candidates after ACL pruning
        fetch_k = min(self.index.ntotal, max(top_k * 4, 50))
        distances, indices = self.index.search(query_vec, fetch_k)

        results: List[Dict[str, Any]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks_metadata):
                continue

            chunk_meta = self.chunks_metadata[idx]
            # Strict ACL Check
            if not acl_service.is_chunk_authorized(user_role, chunk_meta):
                continue

            # In InnerProduct (cosine similarity for normalized vectors), dist is cosine score
            score = float(dist)
            chunk_copy = chunk_meta.copy()
            chunk_copy["dense_score"] = score
            chunk_copy["retrieval_method"] = "dense"
            results.append(chunk_copy)

            if len(results) >= top_k:
                break

        return results
