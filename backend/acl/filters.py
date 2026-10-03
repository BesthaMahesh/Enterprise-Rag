from typing import Dict, Any, List, Optional
from backend.acl.permissions import is_role_in_allowed_roles
from backend.acl.policy import acl_policy_manager


class ACLFilter:
    """Provides filtering logic for dense vectors, BM25 indices, and candidates."""

    @staticmethod
    def filter_chunk_metadata(chunk: Dict[str, Any], user_role: str) -> bool:
        """Evaluate if a single chunk metadata is authorized for the given role."""
        allowed_roles = chunk.get("allowed_roles", [])
        if not is_role_in_allowed_roles(user_role, allowed_roles):
            return False

        classification = chunk.get("classification", "INTERNAL")
        allowed_classifications = acl_policy_manager.get_allowed_classifications(user_role)
        if classification not in allowed_classifications:
            return False

        return True

    @staticmethod
    def get_authorized_chunk_indices(chunks_metadata: List[Dict[str, Any]], user_role: str) -> List[int]:
        """Return array indices of authorized chunks for vector/sparse filtering."""
        authorized_indices = []
        for idx, chunk in enumerate(chunks_metadata):
            if ACLFilter.filter_chunk_metadata(chunk, user_role):
                authorized_indices.append(idx)
        return authorized_indices
