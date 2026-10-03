import pytest
from backend.retrieval.rrf import ReciprocalRankFusion
from backend.reranking.reranker import Reranker


def test_rrf_fusion():
    dense_results = [
        {"chunk_id": "doc1_chk1", "document_title": "Leave Policy", "dense_score": 0.95},
        {"chunk_id": "doc2_chk1", "document_title": "WFH Policy", "dense_score": 0.85}
    ]
    sparse_results = [
        {"chunk_id": "doc2_chk1", "document_title": "WFH Policy", "sparse_score": 5.2},
        {"chunk_id": "doc3_chk1", "document_title": "Travel Policy", "sparse_score": 3.1}
    ]

    fused = ReciprocalRankFusion.fuse(dense_results, sparse_results, rrf_k=60, top_k=5)
    assert len(fused) == 3
    # doc2_chk1 appeared in both, so its RRF score should be highest
    assert fused[0]["chunk_id"] == "doc2_chk1"
    assert fused[0]["rrf_score"] > fused[1]["rrf_score"]


def test_reranker():
    candidates = [
        {"chunk_id": "c1", "content": "Company travel expenses must be approved by manager."},
        {"chunk_id": "c2", "content": "Leave requests must be submitted 2 weeks in advance."}
    ]
    reranked = Reranker.rerank(query="How do I submit leave?", candidates=candidates, top_k=2)
    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c2"
