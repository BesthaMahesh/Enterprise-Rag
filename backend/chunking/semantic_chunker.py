from typing import List, Dict, Any
from backend.metadata.schema import DocumentMetadata
from backend.chunking.structural_chunker import StructuralChunker


class SemanticChunker:
    """
    Semantic chunking layer that leverages structural boundaries and semantic coherence.
    """

    def __init__(self, target_tokens: int = 300, overlap_tokens: int = 40):
        self.structural_chunker = StructuralChunker(target_chunk_size=target_tokens, chunk_overlap=overlap_tokens)

    def chunk_document(self, doc_metadata: DocumentMetadata, sections: list) -> List[Dict[str, Any]]:
        return self.structural_chunker.chunk_sections(doc_metadata, sections)
