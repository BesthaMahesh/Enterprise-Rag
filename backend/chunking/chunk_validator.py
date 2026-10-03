from typing import List, Dict, Any, Tuple
from backend.metadata.schema import ChunkMetadata


class ChunkValidator:
    """Validates that chunks retain all required enterprise metadata and ACL attributes."""

    REQUIRED_FIELDS = [
        "document_id",
        "chunk_id",
        "document_title",
        "section",
        "classification",
        "allowed_roles",
        "version",
        "status"
    ]

    @classmethod
    def validate_chunk(cls, chunk_meta: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        for field in cls.REQUIRED_FIELDS:
            if field not in chunk_meta or chunk_meta[field] is None:
                errors.append(f"Missing required metadata field in chunk: {field}")

        if not isinstance(chunk_meta.get("allowed_roles"), list) or len(chunk_meta.get("allowed_roles", [])) == 0:
            errors.append("Chunk allowed_roles must be a non-empty list.")

        return len(errors) == 0, errors

    @classmethod
    def validate_all_chunks(cls, chunks: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        all_errors = []
        for idx, chunk in enumerate(chunks):
            valid, errors = cls.validate_chunk(chunk)
            if not valid:
                all_errors.extend([f"Chunk #{idx} ({chunk.get('chunk_id', 'unknown')}): {e}" for e in errors])
        return len(all_errors) == 0, all_errors
