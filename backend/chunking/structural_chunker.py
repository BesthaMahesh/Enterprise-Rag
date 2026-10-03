import re
from typing import List, Dict, Any, Optional
from backend.metadata.schema import DocumentMetadata, ChunkMetadata
from backend.ingestion.parsers.document_parser import ParsedSection

try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(tokenizer.encode(text))
except Exception:
    def count_tokens(text: str) -> int:
        return max(1, len(text.split()) * 4 // 3)


class StructuralChunker:
    """
    Splits documents into coherent chunks respecting structural boundaries (headers, paragraphs, tables)
    while strictly binding document-level ACL and metadata to every chunk.
    """

    def __init__(self, target_chunk_size: int = 350, chunk_overlap: int = 50, max_chunk_size: int = 600):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size

    def chunk_sections(self, doc_metadata: DocumentMetadata, sections: List[ParsedSection]) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for sec in sections:
            sec_text = sec.content.strip()
            if not sec_text:
                continue

            sec_tokens = count_tokens(sec_text)

            # If section fits in single chunk
            if sec_tokens <= self.max_chunk_size:
                full_content = f"### {sec.title}\n{sec_text}" if sec.title else sec_text
                chunk_id = f"{doc_metadata.document_id}_chk_{chunk_idx:04d}"
                
                chunk_dict = {
                    "chunk_id": chunk_id,
                    "document_id": doc_metadata.document_id,
                    "document_title": doc_metadata.document,
                    "chunk_index": chunk_idx,
                    "content": full_content,
                    "section": sec.title,
                    "page_number": sec.page,
                    "token_count": count_tokens(full_content),
                    "allowed_roles": doc_metadata.allowed_roles,
                    "classification": doc_metadata.classification,
                    "version": doc_metadata.version,
                    "effective_date": doc_metadata.effective_date,
                    "status": doc_metadata.status,
                    "language": doc_metadata.language,
                    "domain": doc_metadata.domain,
                }
                chunks.append(chunk_dict)
                chunk_idx += 1
            else:
                # Sub-split large section by paragraphs or sentences
                paragraphs = sec_text.split("\n\n")
                current_p_buffer: List[str] = []
                current_p_tokens = 0

                for p in paragraphs:
                    p = p.strip()
                    if not p:
                        continue
                    p_toks = count_tokens(p)

                    if current_p_tokens + p_toks > self.target_chunk_size and current_p_buffer:
                        # Flush current buffer
                        body = "\n\n".join(current_p_buffer)
                        full_content = f"### {sec.title} (Part {chunk_idx + 1})\n{body}"
                        chunk_id = f"{doc_metadata.document_id}_chk_{chunk_idx:04d}"

                        chunks.append({
                            "chunk_id": chunk_id,
                            "document_id": doc_metadata.document_id,
                            "document_title": doc_metadata.document,
                            "chunk_index": chunk_idx,
                            "content": full_content,
                            "section": sec.title,
                            "page_number": sec.page,
                            "token_count": count_tokens(full_content),
                            "allowed_roles": doc_metadata.allowed_roles,
                            "classification": doc_metadata.classification,
                            "version": doc_metadata.version,
                            "effective_date": doc_metadata.effective_date,
                            "status": doc_metadata.status,
                            "language": doc_metadata.language,
                            "domain": doc_metadata.domain,
                        })
                        chunk_idx += 1
                        current_p_buffer = [p]
                        current_p_tokens = p_toks
                    else:
                        current_p_buffer.append(p)
                        current_p_tokens += p_toks

                if current_p_buffer:
                    body = "\n\n".join(current_p_buffer)
                    full_content = f"### {sec.title}\n{body}"
                    chunk_id = f"{doc_metadata.document_id}_chk_{chunk_idx:04d}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "document_id": doc_metadata.document_id,
                        "document_title": doc_metadata.document,
                        "chunk_index": chunk_idx,
                        "content": full_content,
                        "section": sec.title,
                        "page_number": sec.page,
                        "token_count": count_tokens(full_content),
                        "allowed_roles": doc_metadata.allowed_roles,
                        "classification": doc_metadata.classification,
                        "version": doc_metadata.version,
                        "effective_date": doc_metadata.effective_date,
                        "status": doc_metadata.status,
                        "language": doc_metadata.language,
                        "domain": doc_metadata.domain,
                    })
                    chunk_idx += 1

        return chunks
