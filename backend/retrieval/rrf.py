from typing import List, Dict, Any


class ReciprocalRankFusion:
    """
    Combines ranked results from Dense and Sparse retrievers using Reciprocal Rank Fusion (RRF).
    """

    @staticmethod
    def fuse(
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        rrf_k: int = 60,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # Process Dense rankings
        for rank, item in enumerate(dense_results, start=1):
            cid = item["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item.copy()
            else:
                chunk_map[cid]["dense_score"] = item.get("dense_score", 0.0)

        # Process Sparse rankings
        for rank, item in enumerate(sparse_results, start=1):
            cid = item["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item.copy()
            else:
                chunk_map[cid]["sparse_score"] = item.get("sparse_score", 0.0)

        # Build fused list
        fused: List[Dict[str, Any]] = []
        for cid, rrf_score in scores.items():
            chunk = chunk_map[cid]
            chunk["rrf_score"] = rrf_score
            # Default missing scores
            if "dense_score" not in chunk:
                chunk["dense_score"] = 0.0
            if "sparse_score" not in chunk:
                chunk["sparse_score"] = 0.0
            fused.append(chunk)

        # Sort descending by rrf_score
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused[:top_k]
