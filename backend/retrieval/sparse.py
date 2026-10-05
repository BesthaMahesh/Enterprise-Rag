import os
import re
import pickle
import logging
from typing import List, Dict, Any, Tuple, Optional
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

    def check_unauthorized_match(self, query: str, user_role: str) -> Tuple[bool, Optional[str]]:
        """Return private access signal and appropriate contact when the best match is forbidden.

        Distinguishes a request for restricted knowledge from missing evidence.
        No document content or metadata leaves retrieval.
        """
        if self.bm25 is None or not self.corpus_chunks:
            return False, None

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return False, None

        scores = self.bm25.get_scores(query_tokens)
        best_score = max((float(score) for score in scores), default=0.0)

        best_unauthorized_score = 0.0
        query_term_set = {token for token in query_tokens if len(token) >= 4}
        has_strong_unauthorized_term_match = False
        matched_restricted_chunk = None

        for score, chunk in zip(scores, self.corpus_chunks):
            score = float(score)
            if acl_service.is_chunk_authorized(user_role, chunk):
                continue
            if score > best_unauthorized_score:
                best_unauthorized_score = score
                matched_restricted_chunk = chunk
            # BM25 can assign zero IDF to a term in very small corpora. Keep a
            # private, two-term lexical check so a clearly targeted restricted
            # request is still denied rather than mistaken for missing evidence.
            content_terms = set(tokenize_text(chunk.get("content", "")))
            if len(query_term_set & content_terms) >= 2:
                has_strong_unauthorized_term_match = True
                if matched_restricted_chunk is None or score > best_unauthorized_score:
                    matched_restricted_chunk = chunk

        # Require the restricted result to be a leading match. This avoids treating
        # a weak incidental word overlap as an access request.
        is_denied = (
            (best_unauthorized_score > 0.0 and best_unauthorized_score >= best_score * 0.75)
            or (best_score <= 0.0 and has_strong_unauthorized_term_match)
        )
        if not is_denied:
            return False, None

        contact = self._resolve_contact(query, matched_restricted_chunk)
        return True, contact

    def has_unauthorized_match(self, query: str, user_role: str) -> bool:
        """Backward-compatible boolean check."""
        denied, _ = self.check_unauthorized_match(query, user_role)
        return denied

    @staticmethod
    def _resolve_contact(query: str, chunk: Optional[Dict[str, Any]] = None) -> str:
        """Identify contact based on restricted resource without disclosing content/metadata."""
        doc_id = (chunk.get("document_id") or "").lower() if chunk else ""
        classification = (chunk.get("classification") or "").upper() if chunk else ""
        allowed_roles = [str(r).upper() for r in chunk.get("allowed_roles", [])] if chunk else []
        query_lower = query.lower()

        # General restricted / Admin-only resources route to Admin
        if (
            classification == "HIGHLY_RESTRICTED"
            or "admin_restricted" in doc_id
            or (allowed_roles == ["ADMIN"] and "FINANCE" not in allowed_roles)
            or "system architecture" in query_lower
            or "security incident" in query_lower
        ):
            return "Admin"

        # Financial / payroll resources route to Finance
        finance_keywords = [
            "payroll", "salary", "salaries", "financial",
            "budget", "revenue", "expense", "operating expense", "equity", "bonus", "cost"
        ]
        if (
            "finance" in doc_id
            or "payroll" in doc_id
            or "revenue" in doc_id
            or "budget" in doc_id
            or "expense" in doc_id
            or ("FINANCE" in allowed_roles and "EMPLOYEE" not in allowed_roles)
            or any(k in query_lower for k in finance_keywords)
        ):
            return "Finance"

        # HR-specific resources (non-financial) route to HR
        hr_keywords = ["attrition", "disciplinary", "performance review", "recruitment"]
        if (
            any(k in query_lower for k in hr_keywords)
            or "attrition" in doc_id
            or ("HR" in allowed_roles and "FINANCE" not in allowed_roles and "EMPLOYEE" not in allowed_roles)
        ):
            return "HR"

        return "Admin"

