import re
from typing import List, Dict, Any, Tuple
from backend.context.deduplicator import ContextDeduplicator
from backend.context.compressor import ContextCompressor
from backend.context.token_budget import TokenBudgetManager
from backend.acl.service import acl_service


class ContextBuilder:
    """
    Builds the final prompt context block from retrieved candidate chunks
    with deduplication, compression, budgeting, and ACL verification.
    """

    @staticmethod
    def _clean_chunk_content(text: str) -> str:
        if not text:
            return ""
        # Strip header metadata lines that lead the model to quote metadata
        cleaned = re.sub(r"^###?\s*.*?(?:Policy|Handbook|Overview|Guide|Matrix|Plan).*\n?", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"^(?:Version|Effective Date|Classification|Allowed Roles|Owner):.*\n?", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
        cleaned = re.sub(r"^>\s*Synthetic enterprise data.*\n?", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
        cleaned = re.sub(r"Acme Technologies Inc\.?", "the company", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"Acme Technologies", "the company", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bAcme's\b", "the company's", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bAcme\b", "the company", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @classmethod
    def build_context(
        cls,
        query: str,
        raw_candidates: List[Dict[str, Any]],
        user_role: str,
        max_tokens: int = 3000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        # 1. Deduplicate
        deduped = ContextDeduplicator.deduplicate(raw_candidates)

        # 2. Strict pre-LLM ACL check
        authorized_chunks = acl_service.validate_context_before_llm(user_role, deduped)

        # 3. Filter out pure-header / metadata-only chunks with no substantive content
        substantive_chunks = []
        for c in authorized_chunks:
            cleaned = cls._clean_chunk_content(c.get("content", ""))
            body = re.sub(r"^###?\s+.*$", "", cleaned, flags=re.MULTILINE).strip()
            if len(body.split()) >= 8:
                substantive_chunks.append(c)

        chunks_to_budget = substantive_chunks if substantive_chunks else authorized_chunks

        # 4. Compress if chunks are lengthy
        compressed = ContextCompressor.compress(query, chunks_to_budget)

        # 5. Token budgeting
        budgeted = TokenBudgetManager.apply_budget(compressed, max_tokens=max_tokens)

        # 5. Format text block with clean document & section metadata
        context_blocks = []
        for idx, chunk in enumerate(budgeted, start=1):
            doc_title = chunk.get("document_title", "Document")
            sec_name = chunk.get("section", "General")
            raw_content = chunk.get("content", "").strip()
            cleaned_content = cls._clean_chunk_content(raw_content)

            if cleaned_content:
                block = (
                    f"[Document: {doc_title} | Section: {sec_name}]\n"
                    f"{cleaned_content}\n"
                )
                context_blocks.append(block)

        final_context_str = "\n---\n".join(context_blocks)
        return final_context_str, budgeted

