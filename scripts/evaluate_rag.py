import os
import sys
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.session import SessionLocal, init_db
from backend.evaluation.rag_evaluator import RAGEvaluator


def main():
    print("=" * 65)
    print("      ENTERPRISE RAG BENCHMARK & EVALUATION FRAMEWORK")
    print("=" * 65)
    print("Initializing evaluation suite and database...")
    init_db()
    db = SessionLocal()

    evaluator = RAGEvaluator(db=db)
    print("Executing full benchmark dataset against live RAG pipeline...")
    results = evaluator.run_full_evaluation(run_name="Production Hardening Evaluation Benchmark")
    db.close()

    metrics = results["metrics_summary"]
    retrieval = metrics.get("retrieval", {})
    reranking = metrics.get("reranking", {})
    generation = metrics.get("generation", {})
    security = metrics.get("security", {})
    operations = metrics.get("operations", {})

    print("\n" + "=" * 65)
    print(f"EVALUATION REPORT [Run ID: {results['run_id']}]")
    print(f"Total Test Cases: {results['total_questions']} | Passed: {results['passed_count']}/{results['total_questions']}")
    print("=" * 65)

    print("\nRetrieval")
    print(f"Recall@5: {retrieval.get('recall_at_5', 0.0):.3f}")
    print(f"Precision@5: {retrieval.get('precision_at_5', 0.0):.3f}")
    print(f"MRR: {retrieval.get('mrr', 0.0):.3f}")
    print(f"NDCG@5: {retrieval.get('ndcg_at_5', 0.0):.3f}")

    print("\nReranking")
    print(f"MRR: {reranking.get('mrr', 0.0):.3f}")
    print(f"NDCG@5: {reranking.get('ndcg_at_5', 0.0):.3f}")

    print("\nGeneration")
    print(f"Faithfulness: {generation.get('faithfulness', 0.0):.3f}")
    print(f"Groundedness: {generation.get('groundedness', 0.0):.3f}")
    print(f"Answer Relevance: {generation.get('answer_relevance', 0.0):.3f}")
    print(f"Citation Correctness: {generation.get('citation_correctness', 0.0):.3f}")

    print("\nSecurity")
    print(f"ACL violations: {security.get('acl_violation_rate', 0.0):.1%}")
    print(f"Unauthorized retrieval rate: {security.get('unauthorized_retrieval_rate', 0.0):.1%}")
    print(f"Prompt injection detection: {security.get('prompt_injection_detection_rate', 0.0):.1%}")
    print(f"PII leakage: {security.get('pii_leakage_rate', 0.0):.1%}")

    print("\nOperations")
    print(f"Average latency: {operations.get('average_latency_ms', 0.0):.1f} ms")
    print(f"Average tokens: {operations.get('average_tokens', 0.0):.1f}")
    print(f"Estimated cost: ${operations.get('estimated_cost_usd', 0.0):.6f}")
    print(f"Error rate: {operations.get('error_rate', 0.0):.1%}")
    print(f"Total benchmark time: {operations.get('total_time_ms', 0.0):.1f} ms")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
