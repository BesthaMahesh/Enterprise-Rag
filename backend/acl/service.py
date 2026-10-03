import logging
from typing import Dict, Any, List, Tuple, Optional
from backend.acl.filters import ACLFilter
from backend.acl.permissions import is_role_in_allowed_roles
from backend.acl.policy import acl_policy_manager

logger = logging.getLogger(__name__)


class ACLService:
    """
    Centralized ACL enforcement service.
    Guarantees that unauthorized documents and chunks NEVER reach:
    1. Pre-retrieval index scope
    2. Hybrid fusion / Reranking
    3. LLM Prompt Context Construction
    4. Post-generation Output / Citations
    """

    @classmethod
    def is_document_authorized(cls, user_role: str, doc_metadata: Dict[str, Any]) -> bool:
        """Verify if a document is accessible for user role."""
        if not user_role:
            return False
        
        allowed_roles = doc_metadata.get("allowed_roles", [])
        if not is_role_in_allowed_roles(user_role, allowed_roles):
            return False

        classification = doc_metadata.get("classification", "INTERNAL")
        allowed_classifications = acl_policy_manager.get_allowed_classifications(user_role)
        return classification in allowed_classifications

    @classmethod
    def is_chunk_authorized(cls, user_role: str, chunk_metadata: Dict[str, Any]) -> bool:
        """Verify if a chunk is accessible for user role."""
        return ACLFilter.filter_chunk_metadata(chunk_metadata, user_role)

    @classmethod
    def evaluate_chunk_access(cls, user_role: str, chunk: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate access for a chunk and return (is_authorized, reason).
        """
        if not user_role:
            return False, "ANONYMOUS_ACCESS_BLOCKED"

        allowed_roles = chunk.get("allowed_roles", [])
        if not is_role_in_allowed_roles(user_role, allowed_roles):
            return False, "ROLE_NOT_AUTHORIZED"

        classification = chunk.get("classification", "INTERNAL")
        allowed_classifications = acl_policy_manager.get_allowed_classifications(user_role)
        if classification not in allowed_classifications:
            return False, "CLASSIFICATION_RESTRICTED"

        return True, "AUTHORIZED"

    @classmethod
    def filter_authorized_chunks(cls, user_role: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a list of retrieved chunks, strictly keeping only authorized ones with structured audit logging."""
        authorized = []
        for chunk in chunks:
            is_auth, reason = cls.evaluate_chunk_access(user_role, chunk)
            if is_auth:
                authorized.append(chunk)
            else:
                doc_name = (
                    chunk.get("document_title")
                    or chunk.get("document_name")
                    or chunk.get("document")
                    or chunk.get("document_id")
                    or "Unknown Document"
                )
                doc_id = chunk.get("document_id") or doc_name
                chunk_id = chunk.get("chunk_id") or f"{doc_id}#chk"
                classification = chunk.get("classification", "INTERNAL")
                allowed_roles = chunk.get("allowed_roles", [])

                logger.warning(
                    f"ACL Violation Blocked: "
                    f"role={user_role} "
                    f"document={doc_name} "
                    f"chunk_id={chunk_id} "
                    f"classification={classification} "
                    f"allowed_roles={allowed_roles} "
                    f"decision=DENY "
                    f"reason={reason}"
                )
        return authorized

    @classmethod
    def validate_context_before_llm(cls, user_role: str, context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Hard boundary defense: Double-check every chunk right before building prompt context.
        Raises an error or purges immediately if unauthorized chunk is detected.
        """
        verified_chunks = []
        for chunk in context_chunks:
            is_auth, reason = cls.evaluate_chunk_access(user_role, chunk)
            if not is_auth:
                doc_name = chunk.get("document_title") or chunk.get("document_name") or chunk.get("document_id") or "Unknown"
                chunk_id = chunk.get("chunk_id") or "unknown_chunk"
                logger.critical(
                    f"CRITICAL SECURITY ALERT: Unauthorized chunk '{chunk_id}' in doc '{doc_name}' (role={user_role}, reason={reason}) reached pre-LLM context stage. Purging!"
                )
                continue
            verified_chunks.append(chunk)
        return verified_chunks

    @classmethod
    def sanitize_citations_for_role(cls, user_role: str, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure output citations don't leak confidential document titles/metadata to unauthorized roles.
        """
        sanitized = []
        for cit in citations:
            if cls.is_chunk_authorized(user_role, cit):
                sanitized.append(cit)
        return sanitized


acl_service = ACLService()
