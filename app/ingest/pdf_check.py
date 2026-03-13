from pathlib import Path
from pypdf import PdfReader
from pdfminer.high_level import extract_text
from loguru import logger

class PDFCheck:
    @staticmethod
    def is_valid(file_path: Path) -> bool:
        """Checks if the file is a valid PDF using pypdf."""
        try:
            # Pypdf validates header and structure basic
            reader = PdfReader(str(file_path))
            if len(reader.pages) > 0:
                return True
            return False
        except Exception as e:
            logger.warning(f"Invalid PDF {file_path.name}: {e}")
            return False

    @staticmethod
    def has_text(file_path: Path, char_threshold: int = 50) -> bool:
        """
        Determines if the PDF has a usable text layer.
        Extracts text from the first page.
        """
        try:
            # limiting to first page for speed
            text = extract_text(str(file_path), maxpages=1)
            clean_text = text.strip().replace(" ", "")
            
            # Heuristic: if very few characters, it's likely scanned or empty
            has_text_layer = len(clean_text) > char_threshold
            logger.debug(f"File {file_path.name} text check: {len(clean_text)} chars found. Has text? {has_text_layer}")
            
            return has_text_layer
        except Exception as e:
            logger.error(f"Error checking text in {file_path.name}: {e}")
            return False
