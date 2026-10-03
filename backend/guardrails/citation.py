from typing import List, Dict, Any, Tuple
from backend.schemas.chat import SourceCitation


class CitationValidator:
    """Validates citations against retrieved chunks to ensure zero source fabrication."""

    @staticmethod
    def validate_citations(
        citations: List[SourceCitation],
        authorized_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, List[SourceCitation]]:
        valid_doc_ids = {c["document_id"] for c in authorized_chunks}
        valid_citations = []

        for cit in citations:
            if cit.document_id in valid_doc_ids:
                valid_citations.append(cit)

        is_valid = len(valid_citations) > 0 or len(authorized_chunks) == 0
        return is_valid, valid_citations
