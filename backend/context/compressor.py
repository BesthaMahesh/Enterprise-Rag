from typing import List, Dict, Any
import re


class ContextCompressor:
    """Extracts the most relevant sentences/paragraphs matching query terms from retrieved chunks."""

    @staticmethod
    def compress(query: str, chunks: List[Dict[str, Any]], max_chars_per_chunk: int = 1200) -> List[Dict[str, Any]]:
        query_terms = set(re.findall(r"\w+", query.lower()))
        compressed_chunks = []

        for chunk in chunks:
            content = chunk.get("content", "")
            if len(content) <= max_chars_per_chunk:
                compressed_chunks.append(chunk)
                continue

            # Prioritize paragraphs with keyword matches
            paragraphs = content.split("\n\n")
            scored_paras = []
            for p in paragraphs:
                p_lower = p.lower()
                matches = sum(1 for term in query_terms if term in p_lower)
                scored_paras.append((matches, p))

            # Sort by match count descending
            scored_paras.sort(key=lambda x: x[0], reverse=True)

            selected = []
            curr_len = 0
            for _, p in scored_paras:
                if curr_len + len(p) <= max_chars_per_chunk:
                    selected.append(p)
                    curr_len += len(p)
                elif curr_len < 400:
                    selected.append(p[: max_chars_per_chunk - curr_len])
                    break

            chunk_copy = chunk.copy()
            chunk_copy["content"] = "\n\n".join(selected)
            compressed_chunks.append(chunk_copy)

        return compressed_chunks
