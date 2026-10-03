from typing import List, Dict, Any
from backend.retrieval.hybrid import HybridRetriever
from backend.acl.service import acl_service


class EnterpriseRetriever:
    """High-level facade for retrieving authorized enterprise knowledge."""

    def __init__(self):
        self.hybrid_retriever = HybridRetriever()

    def retrieve_authorized_context(self, query: str, user_role: str) -> Dict[str, Any]:
        """
        Retrieves, fuses, and reranks chunks while guaranteeing zero unauthorized chunk leakage.
        """
        # Step 1: Hybrid retrieve with ACL pre-filtering
        results = self.hybrid_retriever.retrieve(query=query, user_role=user_role)

        # Step 2: Defense-in-depth second check before returning candidates
        final_candidates = acl_service.validate_context_before_llm(user_role, results["final_candidates"])
        results["final_candidates"] = final_candidates
        return results


enterprise_retriever = EnterpriseRetriever()
