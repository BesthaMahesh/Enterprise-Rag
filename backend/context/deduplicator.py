from typing import List, Dict, Any
import hashlib


class ContextDeduplicator:
    """Removes duplicate or near-duplicate chunks from retrieved candidates."""

    @staticmethod
    def deduplicate(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_ids = set()
        seen_hashes = set()
        unique_chunks = []

        for chunk in chunks:
            cid = chunk.get("chunk_id")
            if cid in seen_ids:
                continue

            content = chunk.get("content", "").strip()
            # Content normalization hash
            content_norm = "".join(content.split()).lower()
            chash = hashlib.md5(content_norm.encode("utf-8")).hexdigest()
            if chash in seen_hashes:
                continue

            seen_ids.add(cid)
            seen_hashes.add(chash)
            unique_chunks.append(chunk)

        return unique_chunks
