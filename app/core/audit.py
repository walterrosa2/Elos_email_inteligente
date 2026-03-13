import json
from pathlib import Path
from datetime import datetime
from app.core.config import settings
from app.core.logging import logger

class AuditLogger:
    """
    Handles saving of intermediate artifacts (prompts, raw responses) 
    for debugging and development audit.
    Only active if DEV_AUDIT_MODE is True.
    """
    def __init__(self):
        self.enabled = settings.DEV_AUDIT_MODE
        # Base audit path: dados/audit
        self.base_path = settings.DATA_ROOT / "audit"

    def _get_job_path(self, job_id: int, filename: str = None) -> Path:
        """Creates and returns the directory for a specific job, including filename if provided."""
        if not self.enabled:
            return None
        
        folder_name = str(job_id)
        if filename:
            # Sanitize filename: remove extension and invalid chars
            stem = Path(filename).stem
            import re
            clean_stem = re.sub(r'[\<\>\:\"\/\\\|\?\*\x00-\x1f\s]', '_', stem)
            folder_name = f"{job_id}_{clean_stem}"

        path = self.base_path / folder_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(self, job_id: int, step_name: str, data: dict, filename: str = None):
        """Saves a dictionary as a JSON file."""
        if not self.enabled:
            return

        try:
            folder = self._get_job_path(job_id, filename)
            timestamp = datetime.now().strftime("%H%M%S")
            filename_save = f"{step_name}_{timestamp}.json"
            
            file_path = folder / filename_save
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"[AUDIT] Saved {filename_save} for Job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to save audit JSON for Job {job_id}: {e}")

    def save_text(self, job_id: int, step_name: str, text: str, filename: str = None):
        """Saves raw text content."""
        if not self.enabled:
            return

        try:
            folder = self._get_job_path(job_id, filename)
            timestamp = datetime.now().strftime("%H%M%S")
            filename_save = f"{step_name}_{timestamp}.txt"
            
            file_path = folder / filename_save
            file_path.write_text(text, encoding="utf-8")
            
            logger.debug(f"[AUDIT] Saved {filename_save} for Job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to save audit text for Job {job_id}: {e}")

audit = AuditLogger()
