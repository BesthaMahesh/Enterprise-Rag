import re
import unicodedata


class TextCleaner:
    """Cleans, normalizes Unicode, and sanitizes text for RAG processing."""

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode characters (supports English, Telugu, Hindi, etc.)."""
        if not text:
            return ""
        # NFKC standard normalization preserves Indic characters and decomposes compatibility characters
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def clean_text(text: str) -> str:
        """Sanitize text while preserving essential markdown structures."""
        if not text:
            return ""

        text = TextCleaner.normalize_unicode(text)
        
        # Replace carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Remove null bytes or control characters except newlines and tabs
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        
        # Collapse multiple empty lines to max 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Strip trailing whitespaces per line
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines).strip()
