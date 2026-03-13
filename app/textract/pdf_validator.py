from pypdf import PdfReader
from io import BytesIO
from app.core.logging import logger

class PDFValidator:
    @staticmethod
    def validate(file_bytes: bytes) -> dict:
        """
        Validates if bytes are a valid PDF.
        Returns dict with valid (bool), pages (int), and error (str).
        """
        try:
            stream = BytesIO(file_bytes)
            reader = PdfReader(stream)
            
            if reader.is_encrypted:
                return {"valid": False, "pages": 0, "error": "Encrypted PDF"}
                
            pages = len(reader.pages)
            if pages == 0:
                 return {"valid": False, "pages": 0, "error": "Empty PDF"}

            return {"valid": True, "pages": pages, "error": None}
            
        except Exception as e:
            logger.warning(f"PDF Validation failed: {e}")
            return {"valid": False, "pages": 0, "error": str(e)}

    @staticmethod
    def is_pdf(filename: str) -> bool:
        return filename.lower().endswith('.pdf')
