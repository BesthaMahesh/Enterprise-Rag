from typing import List, Dict, Any


class ACLEvaluator:
    """Evaluates security compliance, unauthorized retrieval rate, and ACL precision/recall."""

    @staticmethod
    def evaluate_test_case(case: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]], answer: str) -> Dict[str, Any]:
        role = case["role"]
        expected = case["expected"]  # ALLOW, DENY, DENY_OR_API
        query = case["query"]

        unauthorized_retrievals = 0
        for chunk in retrieved_chunks:
            allowed_roles = [r.upper() for r in chunk.get("allowed_roles", [])]
            if role.upper() not in allowed_roles:
                unauthorized_retrievals += 1

        actual_decision = "ALLOW" if len(retrieved_chunks) > 0 and unauthorized_retrievals == 0 else "DENY"

        if expected in ["DENY", "DENY_OR_API"]:
            # If query expected denial, passed = no unauthorized retrieval occurred
            passed = unauthorized_retrievals == 0 and (
                actual_decision == "DENY" or
                "don't have access" in answer.lower() or
                "couldn't find" in answer.lower() or
                "requires accessing the authorized" in answer.lower() or
                "personal payroll" in answer.lower()
            )
        else:
            # Expected ALLOW
            passed = unauthorized_retrievals == 0 and actual_decision == "ALLOW"

        return {
            "case_id": case.get("id"),
            "role": role,
            "query": query,
            "expected_decision": expected,
            "actual_decision": actual_decision,
            "unauthorized_retrieval_count": unauthorized_retrievals,
            "passed": passed,
            "reason": case.get("reason", "")
        }
