from typing import Tuple, List, Dict, Any
from backend.metadata.schema import DocumentMetadata


class DocumentValidator:
    """Validates raw documents and metadata before chunking and embedding."""

    @staticmethod
    def validate_document(content: str, metadata: DocumentMetadata) -> Tuple[bool, List[str]]:
        errors = []
        if not content or len(content.strip()) < 10:
            errors.append("Document content is too short or empty (< 10 characters).")

        if not metadata.document_id:
            errors.append("Missing required field: document_id.")

        if not metadata.document:
            errors.append("Missing required field: document title.")

        if not metadata.allowed_roles or len(metadata.allowed_roles) == 0:
            errors.append("Document must have at least one allowed role in allowed_roles.")

        valid_classifications = ["INTERNAL", "CONFIDENTIAL", "RESTRICTED", "HIGHLY_RESTRICTED"]
        if metadata.classification not in valid_classifications:
            errors.append(f"Invalid classification '{metadata.classification}'. Must be one of {valid_classifications}")

        return (len(errors) == 0, errors)
