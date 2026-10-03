from typing import List, Dict, Any
from backend.retrieval.dense import DenseRetriever
from backend.retrieval.sparse import SparseRetriever
from backend.retrieval.rrf import ReciprocalRankFusion
from backend.reranking.reranker import Reranker
from backend.config.settings import settings


class HybridRetriever:
    """
    Coordinates Dense Vector Retrieval, BM25 Sparse Retrieval, Reciprocal Rank Fusion,
    and Cross-Encoder Reranking, strictly scoped by role ACL.
    """

    def __init__(self, dense_retriever: DenseRetriever = None, sparse_retriever: SparseRetriever = None):
        self.dense = dense_retriever or DenseRetriever()
        self.sparse = sparse_retriever or SparseRetriever()

    def retrieve(
        self,
        query: str,
        user_role: str,
        top_k_dense: int = None,
        top_k_sparse: int = None,
        top_k_rerank: int = None,
        final_k: int = None
    ) -> Dict[str, Any]:
        k_dense = top_k_dense or settings.TOP_K_DENSE
        k_sparse = top_k_sparse or settings.TOP_K_SPARSE
        k_rerank = top_k_rerank or settings.TOP_K_RERANK
        k_final = final_k or settings.FINAL_CONTEXT_K

        # Low memory mode bypasses PyTorch to guarantee operation under 100MB RAM
        if getattr(settings, "LOW_MEMORY_MODE", False):
            sparse_results = self.sparse.search(query, user_role=user_role, top_k=k_final)
            return {
                "dense_results": [],
                "sparse_results": sparse_results,
                "fused_results": sparse_results,
                "reranked_results": sparse_results,
                "final_candidates": sparse_results
            }

        # Step 1: Run Dense Retrieval (ACL filtered)
        dense_results = self.dense.search(query, user_role=user_role, top_k=k_dense)

        # Step 2: Run BM25 Sparse Retrieval (ACL filtered)
        sparse_results = self.sparse.search(query, user_role=user_role, top_k=k_sparse)

        # Step 3: Reciprocal Rank Fusion
        fused_candidates = ReciprocalRankFusion.fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            rrf_k=settings.RRF_K,
            top_k=k_dense + k_sparse
        )

        # Step 4: Cross-Encoder Reranking
        reranked_results = Reranker.rerank(
            query=query,
            candidates=fused_candidates,
            top_k=k_rerank
        )

        # Final top K candidates
        final_candidates = reranked_results[:k_final]

        return {
            "dense_results": dense_results,
            "sparse_results": sparse_results,
            "fused_results": fused_candidates,
            "reranked_results": reranked_results,
            "final_candidates": final_candidates
        }
