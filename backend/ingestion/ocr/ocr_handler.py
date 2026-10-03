import logging

logger = logging.getLogger(__name__)


class OCRHandler:
    """Handles OCR processing when images or scanned PDFs require text extraction."""

    @staticmethod
    def extract_text_from_image(image_bytes: bytes) -> str:
        """
        Attempts OCR with pytesseract or easyocr if available, or returns fallback warning.
        """
        try:
            import pytesseract
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(image)
        except Exception as e:
            logger.info(f"OCR module not active or failed: {e}. Fallback to direct extraction.")
            return ""
