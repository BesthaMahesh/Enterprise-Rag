import os
import json
from typing import List, Dict, Any


class EvaluationDatasetLoader:
    """Loads benchmark test sets for ACL enforcement and RAG quality."""

    @staticmethod
    def load_acl_test_cases(file_path: str = "data/evaluation/acl_test_cases.json") -> List[Dict[str, Any]]:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def load_rag_questions(file_path: str = "data/evaluation/rag_evaluation_questions.json") -> List[str]:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def load_benchmark_dataset(file_path: str = "data/evaluation/rag_eval_dataset.json") -> List[Dict[str, Any]]:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
