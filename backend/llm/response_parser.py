import re
from typing import List, Dict, Any, Tuple
from backend.schemas.chat import SourceCitation


class ResponseParser:
    """Parses raw LLM generated text and extracts structured citations and answer body."""

    @staticmethod
    def parse_response(
        llm_output: str,
        retrieved_chunks: List[Dict[str, Any]],
        user_role: str
    ) -> Tuple[str, List[SourceCitation]]:
        if not llm_output:
            return "", []

        # Split answer and explicit source section if present (handles **Sources**, Sources:, etc.)
        source_pattern = re.compile(
            r"(?i)\n+(?:\*{1,2}|#{1,4})?\s*(?:Sources?|References?):?\s*(?:\*{1,2})?\s*\n*",
            re.DOTALL
        )
        parts = source_pattern.split(llm_output, maxsplit=1)
        answer_text = parts[0].strip()

        # Normalize unicode non-breaking spaces and hyphens
        answer_text = answer_text.replace('\u202f', ' ').replace('\u00a0', ' ')
        answer_text = answer_text.replace('\u2011', '-')

        # Remove literal '(Source \d+)' or '[Source \d+]' tags
        answer_text = re.sub(r"\s*[\(\[]Source\s*\d+[\)\]]", "", answer_text, flags=re.IGNORECASE)

        # Remove dangling markdown symbols or quotes at the end
        answer_text = re.sub(r"\n+\s*(?:\*\*|\*|##|\^\^)+\s*$", "", answer_text)

        # Remove accidental raw metadata lines like "- **Document details**..."
        answer_text = re.sub(r"(?m)^\s*-\s*\*\*Document details\*\*.*?\n?", "", answer_text)

        # Neutralize any specific company names
        answer_text = re.sub(r"Acme Technologies Inc\.?", "the company", answer_text, flags=re.IGNORECASE)
        answer_text = re.sub(r"Acme Technologies", "the company", answer_text, flags=re.IGNORECASE)
        answer_text = re.sub(r"\bAcme's\b", "the company's", answer_text, flags=re.IGNORECASE)
        answer_text = re.sub(r"\bAcme\b", "the company", answer_text, flags=re.IGNORECASE)

        # Match chunks that contributed to the context
        # Group and deduplicate by document_title to ensure clean citations
        doc_map: Dict[str, Dict[str, Any]] = {}

        for chunk in retrieved_chunks:
            doc_id = chunk.get("document_id") or "doc"
            doc_title = chunk.get("document_title", "Document")
            sec_name = chunk.get("section", "General") or "General"
            sec_name = re.sub(r"Acme Technologies\s*[\u2014\-]\s*", "", sec_name, flags=re.IGNORECASE).strip()
            if not sec_name:
                sec_name = "Overview"
            classification = chunk.get("classification", "INTERNAL")
            score = chunk.get("reranker_score", chunk.get("dense_score", 0.9))

            # Strip metadata preamble from snippet
            content = chunk.get("content", "").strip()
            content_cleaned = re.sub(r"^###?\s*.*?(?:Policy|Handbook|Overview|Guide|Matrix|Plan).*\n?", "", content, flags=re.MULTILINE)
            content_cleaned = re.sub(r"^(?:Version|Effective Date|Classification|Allowed Roles|Owner):.*\n?", "", content_cleaned, flags=re.MULTILINE | re.IGNORECASE)
            content_cleaned = re.sub(r"^>\s*Synthetic enterprise data.*\n?", "", content_cleaned, flags=re.MULTILINE | re.IGNORECASE)
            content_cleaned = re.sub(r"Acme Technologies Inc\.?", "the company", content_cleaned, flags=re.IGNORECASE)
            content_cleaned = re.sub(r"Acme Technologies", "the company", content_cleaned, flags=re.IGNORECASE)
            content_cleaned = re.sub(r"\bAcme\b", "the company", content_cleaned, flags=re.IGNORECASE).strip()

            snippet = content_cleaned[:300] + ("..." if len(content_cleaned) > 300 else "")

            # Group per document
            if doc_title not in doc_map:
                doc_map[doc_title] = {
                    "document_id": doc_id,
                    "document_title": doc_title,
                    "sections": [sec_name] if sec_name else ["General"],
                    "classification": classification,
                    "snippet": snippet,
                    "relevance_score": score,
                    "allowed_roles": chunk.get("allowed_roles", [])
                }
            else:
                existing = doc_map[doc_title]
                if sec_name and sec_name not in existing["sections"]:
                    existing["sections"].append(sec_name)
                if score is not None and (existing["relevance_score"] is None or score > existing["relevance_score"]):
                    existing["relevance_score"] = score

        citations: List[SourceCitation] = []
        for d in doc_map.values():
            sections_str = ", ".join(d["sections"][:3])
            citations.append(SourceCitation(
                document_id=d["document_id"],
                document_title=d["document_title"],
                section=sections_str,
                page_number=1,
                classification=d["classification"],
                snippet=d["snippet"],
                relevance_score=round(float(d["relevance_score"]), 3) if d["relevance_score"] is not None else 0.9,
                allowed_roles=d["allowed_roles"]
            ))

        return answer_text.strip(), citations


