import os
import re
import pickle
import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from backend.acl.service import acl_service
from backend.config.settings import settings

logger = logging.getLogger(__name__)


def tokenize_text(text: str) -> List[str]:
    """
    Multilingual tokenizer supporting alphanumeric words, Indic scripts, and special terms.
    """
    if not text:
        return []
    # Tokenize words, digits, and non-ASCII unicode character sequences
    tokens = re.findall(r"\w+", text.lower(), re.UNICODE)
    return tokens


class SparseRetriever:
    """
    BM25 Sparse Retriever with ACL filtering.
    """

    def __init__(self, index_path: str = None):
        self.index_path = index_path or settings.BM25_INDEX_PATH
        self.bm25: BM25Okapi = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.load_index()

    def load_index(self):
        """Load BM25 model and corpus from disk."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data.get("bm25")
                    self.corpus_chunks = data.get("corpus_chunks", [])
                logger.info(f"Loaded BM25 index with {len(self.corpus_chunks)} documents.")
            except Exception as e:
                logger.error(f"Error loading BM25 index: {e}")
                self.bm25 = None
                self.corpus_chunks = []

    def save_index(self, corpus_chunks: List[Dict[str, Any]]):
        """Build and save BM25 index."""
        tokenized_corpus = [tokenize_text(c["content"]) for c in corpus_chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus_chunks = corpus_chunks

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "corpus_chunks": self.corpus_chunks
            }, f)
        logger.info(f"Saved BM25 index with {len(corpus_chunks)} chunks.")

    def search(self, query: str, user_role: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        BM25 search strictly filtered by user role ACL.
        """
        if self.bm25 is None or len(self.corpus_chunks) == 0:
            return []

        tokenized_query = tokenize_text(query)
        if not tokenized_query:
            return []

        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Sort indices by score descending
        sorted_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)

        results: List[Dict[str, Any]] = []
        for idx in sorted_indices:
            score = float(doc_scores[idx])
            if score <= 0.0:
                break

            chunk_meta = self.corpus_chunks[idx]
            # Strict ACL check
            if not acl_service.is_chunk_authorized(user_role, chunk_meta):
                continue

            chunk_copy = chunk_meta.copy()
            chunk_copy["sparse_score"] = score
            chunk_copy["retrieval_method"] = "sparse"
            results.append(chunk_copy)

            if len(results) >= top_k:
                break

        return results
