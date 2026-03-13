import hashlib
from pathlib import Path
from datetime import datetime
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import List
from loguru import logger
from app.core.config import settings
from app.core.models import Origem

class StagingService:
    """
    Responsible for handling the initial download of attachments 
    and saving metadata (provenance).
    """

    def process_message(self, email_obj: Message, msg_imap_id: int) -> List[Path]:
        """
        Extracts PDF attachments from the email, saves them to the
        staging folder (originais) organized by date, and creates
        provenance JSON files.
        """
        
        # 1. Determine Date and Paths
        email_date_header = email_obj.get("Date")
        try:
            if email_date_header:
                dt_email = parsedate_to_datetime(email_date_header)
                # Convert to naive or timezone aware as per settings?
                # parsedate_to_datetime returns aware if timezone is in string.
                # simpler to just use it for folder structure:
            else:
                dt_email = datetime.now()
                logger.warning(f"Email {msg_imap_id} has no Date header. Using now().")
        except Exception as e:
            logger.error(f"Error parsing date for {msg_imap_id}: {e}")
            dt_email = datetime.now()

        # Structure: root/YYYY/MM/DD
        day_folder = settings.DATA_ROOT / f"{dt_email.year}" / f"{dt_email.month:02d}" / f"{dt_email.day:02d}"
        path_originais = day_folder / "originais"
        path_json = day_folder / "json" # For provenance/meta files initially
        path_ignorados = day_folder / "ignorados"

        for p in [path_originais, path_json, path_ignorados]:
            p.mkdir(parents=True, exist_ok=True)

        saved_pdfs = []

        # 2. Iterate Attachments
        for part in email_obj.walk():
            # multiparts are containers, we want leaves
            if part.get_content_maintype() == 'multipart':
                continue
                
            content_disposition = part.get("Content-Disposition", "")
            if not content_disposition:
                continue
                
            filename = part.get_filename()
            if not filename:
                continue

            # 3. Check for PDF (Case insensitive)
            if not filename.lower().endswith('.pdf'):
                # Optional: Save non-pdf to 'ignorados' logic here if desired
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue
            
            # 4. Hash and Dedupe Check
            file_hash = hashlib.sha256(payload).hexdigest()
            
            # Sanitizing filename
            safe_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ','.','_','-')]).strip()
            # Prefix with msg_id to ensure uniqueness if same filename in different emails (though hash checks duplicate content)
            # Reqs: "Chave correlação: MSG_ID + nome + SHA256"
            
            final_filename = f"{msg_imap_id}_{safe_filename}"
            target_path = path_originais / final_filename
            
            # Write PDF
            if target_path.exists():
                logger.info(f"File {final_filename} already exists. Overwriting/Checking hash...")
                # If content is different, might want to handle renaming, but for now strict overwrite or skip?
                # Let's overwrite to ensure latest state or skip? 
                # Reqs say "De-dupe". We'll rely on downstream dedupe or hash check.
            
            with open(target_path, "wb") as f:
                f.write(payload)
            
            saved_pdfs.append(target_path)
            
            # 5. Create Metadata (Origem)
            try:
                subject_str = str(email_obj.get("Subject", ""))
                from_str = str(email_obj.get("From", ""))
                
                origem = Origem(
                    dt_email=dt_email,
                    msg_id=str(msg_imap_id),
                    remetente=from_str,
                    assunto=subject_str,
                    arquivo=safe_filename,
                    hash_arquivo=file_hash,
                    caminho_original=str(target_path.absolute())
                )
                
                # Save JSON provenance
                meta_filename = f"{target_path.stem}_origem.json"
                meta_path = path_json / meta_filename
                
                with open(meta_path, "w", encoding="utf-8") as f:
                    f.write(origem.model_dump_json(indent=2))
                    
            except Exception as e:
                logger.error(f"Failed to save metadata for {final_filename}: {e}")

        return saved_pdfs
