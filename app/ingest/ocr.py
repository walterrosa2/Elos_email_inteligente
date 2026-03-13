import shutil
import subprocess
from pathlib import Path
from loguru import logger
from app.core.config import settings

class OCRProcessor:
    """
    Wraps ocrmypdf execution.
    """
    
    def __init__(self):
        self.lang = settings.OCR_LANG

    def ensure_searchable(self, input_path: Path, output_path: Path) -> bool:
        """
        Runs OCR on input_path and saves to output_path.
        If OCR fails (e.g. tool not installed), copies original as fallback.
        Returns True if OCR ran (or attempted), False if just copied.
        
        Note: ocrmypdf with --skip-text will detect if text exists and skip actual OCR,
        but still re-generates the PDF.
        """
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            logger.info(f"Target file {output_path.name} already exists. Skipping OCR.")
            return True

        # Check if ocrmypdf is in PATH
        if not shutil.which("ocrmypdf"):
            logger.warning("ocrmypdf not found in PATH. Skipping OCR and copying original.")
            shutil.copy2(input_path, output_path)
            return False

        try:
            logger.info(f"Starting OCR for {input_path.name}...")
            
            # Command construction
            # --skip-text: keeps existing text, only OCRs images.
            # --tesseract-timeout: prevent hangs
            command = [
                "ocrmypdf",
                "--skip-text", 
                "--jobs", "2", 
                "--language", self.lang,
                "--output-type", "pdf",
                "--optimize", "1",
                str(input_path),
                str(output_path)
            ]
            
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"OCR completed successfully for {input_path.name}")
                return True
            else:
                logger.error(f"OCR process returned error: {result.stderr}")
                # Fallback copy
                shutil.copy2(input_path, output_path)
                return False
                
        except Exception as e:
            logger.exception(f"Exception running OCR for {input_path.name}: {e}")
            shutil.copy2(input_path, output_path)
            return False
