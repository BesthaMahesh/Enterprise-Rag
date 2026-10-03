import json
import os
from typing import Dict, List, Set


DEFAULT_POLICY = {
    "roles": {
        "EMPLOYEE": ["INTERNAL"],
        "HR": ["INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
        "FINANCE": ["INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
        "ADMIN": ["INTERNAL", "CONFIDENTIAL", "RESTRICTED", "HIGHLY_RESTRICTED"],
        "SECURITY": ["INTERNAL", "HIGHLY_RESTRICTED"]
    },
    "rule": "Filter documents by authenticated role and document allowed_roles before retrieval/context construction."
}


class ACLPolicyManager:
    """Manages system-wide ACL policies loaded from configuration or json files."""

    def __init__(self, policy_file: str = "data/acl/acl_policy.json"):
        self.policy_file = policy_file
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict:
        if os.path.exists(self.policy_file):
            try:
                with open(self.policy_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return DEFAULT_POLICY
        return DEFAULT_POLICY

    def get_allowed_classifications(self, role: str) -> Set[str]:
        roles_map = self.policy.get("roles", {})
        return set(roles_map.get(role, ["INTERNAL"]))


acl_policy_manager = ACLPolicyManager()
