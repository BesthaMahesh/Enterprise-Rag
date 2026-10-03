import os
from typing import Tuple, Dict, Any


class FileLoader:
    """Loads documents from various file formats (.md, .txt, .pdf, .docx)."""

    @staticmethod
    def load(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Load file and return (raw_text, file_metadata)."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()
        file_size = os.path.getsize(file_path)
        metadata = {
            "file_name": file_name,
            "file_path": file_path,
            "file_size_bytes": file_size,
            "extension": ext
        }

        if ext in [".md", ".markdown", ".txt", ".json", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return content, metadata

        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    pages_text.append(f"<!-- Page {idx + 1} -->\n{page_text}")
                content = "\n\n".join(pages_text)
                metadata["page_count"] = len(reader.pages)
                return content, metadata
            except Exception as e:
                raise RuntimeError(f"Error loading PDF {file_path}: {e}")

        elif ext in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                content = "\n\n".join(paragraphs)
                return content, metadata
            except Exception:
                # Basic binary fallback
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return content, metadata

        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return content, metadata
