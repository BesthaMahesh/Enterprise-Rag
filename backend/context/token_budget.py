import logging
from typing import List, Dict, Any
from backend.chunking.structural_chunker import count_tokens
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class TokenBudgetManager:
    """Enforces strict token limits for context injected into LLM prompts."""

    @staticmethod
    def apply_budget(
        chunks: List[Dict[str, Any]],
        max_tokens: int = None
    ) -> List[Dict[str, Any]]:
        budget = max_tokens or settings.MAX_CONTEXT_TOKENS
        accumulated_tokens = 0
        budgeted_chunks = []

        for chunk in chunks:
            content = chunk.get("content", "")
            tok_count = chunk.get("token_count") or count_tokens(content)

            if accumulated_tokens + tok_count <= budget:
                budgeted_chunks.append(chunk)
                accumulated_tokens += tok_count
            else:
                remaining_tokens = budget - accumulated_tokens
                if remaining_tokens > 60:
                    # Truncate content to fit remaining budget
                    words = content.split()
                    truncated_words = words[: remaining_tokens * 3 // 4]
                    truncated_content = " ".join(truncated_words) + " ... [truncated]"
                    chunk_copy = chunk.copy()
                    chunk_copy["content"] = truncated_content
                    chunk_copy["token_count"] = remaining_tokens
                    budgeted_chunks.append(chunk_copy)
                    accumulated_tokens += remaining_tokens
                break

        return budgeted_chunks
