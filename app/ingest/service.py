from datetime import date
from typing import Optional
from email.utils import parsedate_to_datetime
from email.header import decode_header
import re
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.config import settings
from app.db.models import Job
from app.storage.local_adapter import storage
from app.email_client.imap_service import IMAPService
from app.core.settings_service import settings_service
from pathlib import Path

class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.imap = IMAPService()

    def _sanitize_filename(self, filename: str) -> str:
        """Decodes MIME encoded filenames and removes illegal characters."""
        if not filename:
            return "unnamed_attachment"
            
        # 1. Decode MIME (e.g. =?utf-8?B?...)
        decoded_parts = decode_header(filename)
        clean_name = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                clean_name += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                clean_name += part
        
        # 2. Remove Windows illegal characters / control chars
        # Illegal: < > : " / \ | ? * and control chars 0-31
        clean_name = re.sub(r'[\<\>\:\"\/\\\|\?\*\x00-\x1f]', '_', clean_name)
        # Remove newlines and carriage returns specifically
        clean_name = clean_name.replace('\r', '').replace('\n', '')
        
        return clean_name.strip()

    def process_new_emails(self, start_date: Optional[date] = None, end_date: Optional[date] = None):
        """Fetches emails and creates jobs for attachments."""
        try:
            pwd = settings.IMAP_PASSWORD if not settings.USE_OAUTH2 else None
            self.imap.connect(password=pwd)
            msg_ids = self.imap.search_candidates(start_date=start_date, end_date=end_date) 
            
            processed_count = 0
            skipped_count = 0

            def decode_mime(text):
                if not text: return text
                try:
                    decoded_parts = decode_header(text)
                    result = ""
                    for part, encoding in decoded_parts:
                        if isinstance(part, bytes):
                            # Try encoding, fallback to robust Brazilian charsets
                            charsets = [encoding, 'utf-8', 'iso-8859-1', 'windows-1252', 'latin-1']
                            decoded = False
                            for c in charsets:
                                if not c: continue
                                try:
                                    result += part.decode(c)
                                    decoded = True
                                    break
                                except:
                                    continue
                            if not decoded:
                                result += part.decode('utf-8', errors='ignore')
                        else:
                            result += str(part)
                    return result
                except:
                    return text

            for msg_id in msg_ids:
                message_data = self.imap.fetch_message_data(msg_id)
                if not message_data:
                    continue

                email_obj = message_data["email_object"]
                
                # Determine email_msg_id ONCE
                email_msg_id = email_obj.get("Message-ID")
                if not email_msg_id:
                     email_msg_id = f"{message_data.get('from', '')}_{message_data.get('msg_id')}"
                
                # --- V3: EMAIL CONTEXT UPSERT (Captured for ALL emails) ---
                from app.db.models import EmailContext
                ctx = self.db.query(EmailContext).filter(EmailContext.message_id == email_msg_id).first()
                if not ctx:
                    body_content = self.imap.get_email_body(email_obj)
                    ctx = EmailContext(
                        message_id=email_msg_id,
                        subject=decode_mime(message_data.get("subject")),
                        sender=message_data.get("from"),
                        received_at=parsedate_to_datetime(email_obj["Date"]) if email_obj["Date"] else None,
                        body_text=body_content
                    )
                    self.db.add(ctx)
                    self.db.commit()
                    logger.info(f"Created EmailContext for msg {email_msg_id}")

                # Extract Attachments
                for part in email_obj.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    raw_filename = part.get_filename()
                    if not raw_filename:
                        continue
                    
                    filename = self._sanitize_filename(raw_filename)

                    # --- FILTER BY EXTENSION ---
                    ext = Path(filename).suffix.lower()
                    
                    # Skip files without extension (inline images, etc)
                    if not ext:
                        logger.debug(f"File {filename} has no extension. Skipping.")
                        continue
                    
                    allowed_exts = settings_service.get_allowed_extensions()
                    
                    if ext not in [e.lower() for e in allowed_exts]:
                        logger.debug(f"Extension {ext} not allowed for {filename}. Skipping.")
                        continue

                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue

                    # Determine Date for Storage Path
                    from datetime import datetime
                    email_date_obj = None
                    if message_data.get("date"):
                        try:
                            email_date_obj = parsedate_to_datetime(message_data["date"])
                        except:
                            pass
                    
                    ref_date = email_date_obj if email_date_obj else datetime.now()
                    date_subfolder = ref_date.strftime("%Y/%m/%d")

                    # Save to storage
                    storage_meta = storage.save_file(payload, filename, date_subfolder=date_subfolder)
                    file_hash = storage_meta["attachment_hash"]
                    
                    job_unique_hash = f"{email_msg_id}_{file_hash}"
                    
                    existing_job = self.db.query(Job).filter(Job.job_hash == job_unique_hash).first()
                    
                    if existing_job:
                        logger.debug(f"Job already exists for {filename}. Skipping.")
                        skipped_count += 1
                        continue
                    
                    # Create Job
                    new_job = Job(
                        job_hash=job_unique_hash,
                        message_id=email_msg_id,
                        sender=message_data.get("from"),
                        subject=decode_mime(message_data.get("subject")),
                        email_date=ctx.received_at,
                        received_at=ctx.received_at,
                        attachment_name=filename,
                        attachment_hash=file_hash,
                        storage_uri=storage_meta["storage_uri"],
                        status="STAGED"
                    )
                    
                    self.db.add(new_job)
                    self.db.commit()
                    logger.info(f"Created Job {new_job.id} for {filename}")
                    processed_count += 1

            logger.info(f"Ingestion cycle finish. Processed jobs: {processed_count}, Skipped jobs: {skipped_count}")

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
        finally:
            self.imap.disconnect()
