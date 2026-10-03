import math
from typing import List, Set


class RetrievalMetrics:
    """Calculates standard IR metrics: Recall@K, Precision@K, MRR, NDCG."""

    @staticmethod
    def precision_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: Set[str], k: int) -> float:
        if k <= 0 or not retrieved_doc_ids:
            return 0.0
        top_k = retrieved_doc_ids[:k]
        hits = sum(1 for doc in top_k if doc in relevant_doc_ids)
        return hits / float(k)

    @staticmethod
    def recall_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: Set[str], k: int) -> float:
        if not relevant_doc_ids:
            return 1.0
        top_k = retrieved_doc_ids[:k]
        hits = len(set(top_k).intersection(relevant_doc_ids))
        return min(1.0, hits / float(len(relevant_doc_ids)))

    @staticmethod
    def mrr(retrieved_doc_ids: List[str], relevant_doc_ids: Set[str]) -> float:
        for rank, doc in enumerate(retrieved_doc_ids, start=1):
            if doc in relevant_doc_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: Set[str], k: int) -> float:
        top_k = retrieved_doc_ids[:k]
        dcg = 0.0
        for i, doc in enumerate(top_k, start=1):
            rel = 1.0 if doc in relevant_doc_ids else 0.0
            dcg += (2**rel - 1) / math.log2(i + 1)

        # Ideal DCG
        ideal_rels = sorted([1.0 if d in relevant_doc_ids else 0.0 for d in top_k], reverse=True)
        idcg = sum((2**rel - 1) / math.log2(i + 1) for i, rel in enumerate(ideal_rels, start=1))

        if idcg == 0.0:
            return 0.0
        return dcg / idcg
