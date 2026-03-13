import boto3
from typing import Dict, Any, List
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.logging import logger

class TextractService:
    def __init__(self):
        self.client = boto3.client(
            "textract",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def process_document(self, file_bytes: bytes, use_async: bool = False, job_id: int = None, filename: str = None) -> Dict[str, Any]:
        """
        Main entry point. Decides between sync and async (or force async).
        Returns the simplified text result and raw blocks.
        """
        try:
            if use_async:
                # Async requires S3 upload first. For V2.1 MVP we might want to stick to Sync 
                # or implement S3 upload logic.
                # PRD mentions fallback. Let's assume we implement Sync first and Async if needed
                # or if file is too big (Textract Sync limit is ~5MB-10MB).
                raise NotImplementedError("Async mode requires S3 integration - pending implementation.")
            
            return self._process_sync(file_bytes, job_id=job_id, filename=filename)

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['RequestTooLargeException', 'ProvisionedThroughputExceededException']:
                logger.warning(f"Sync processing failed ({error_code}). Falling back to Async (Not Implemented).")
                # Here we would trigger async
                raise e 
            else:
                logger.error(f"Textract Error: {e}")
                raise

    def process_document_multipage(self, file_bytes: bytes, job_id: int = None, filename: str = None) -> Dict[str, Any]:
        """
        Splits PDF into individual pages and processes each page using Sync Textract.
        Aggregates results into a single response.
        """
        from pypdf import PdfReader, PdfWriter
        import io

        fname = filename.lower() if filename else ""
        if not fname.endswith(".pdf"):
            return self._process_sync(file_bytes, job_id=job_id, filename=filename)

        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            
            if total_pages <= 1:
                return self._process_sync(file_bytes, job_id=job_id, filename=filename)

            logger.info(f"Processing multipage PDF ({total_pages} pages) for {filename}")
            
            combined_text = []
            combined_blocks = []
            
            for i in range(total_pages):
                logger.info(f"Processing page {i+1}/{total_pages} of {filename}...")
                
                # Create a 1-page PDF
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                
                page_buffer = io.BytesIO()
                writer.write(page_buffer)
                page_bytes = page_buffer.getvalue()
                
                # Process single page
                try:
                    res = self._process_sync(page_bytes, job_id=job_id, filename=f"{filename}_p{i+1}")
                    combined_text.append(f"--- PAGE {i+1} ---\n" + res["text"])
                    combined_blocks.extend(res["blocks"])
                except Exception as page_err:
                    logger.error(f"Failed to process page {i+1} of {filename}: {page_err}")
                    combined_text.append(f"--- PAGE {i+1} ERROR: {str(page_err)} ---")

            return {
                "text": "\n\n".join(combined_text),
                "blocks": combined_blocks,
                "pages": total_pages
            }

        except Exception as e:
            logger.error(f"Error splitting PDF {filename}: {e}")
            # Fallback to sync direct if split fails
            return self._process_sync(file_bytes, job_id=job_id, filename=filename)

    def _process_sync(self, file_bytes: bytes, job_id: int = None, filename: str = None) -> Dict[str, Any]:
        """Call Textract Synchronous API."""
        logger.info("Starting Sync Textract processing...")
        response = self.client.detect_document_text(
            Document={'Bytes': file_bytes}
        )
        
        # Audit: Save Raw Textract Response
        if job_id:
            from app.core.audit import audit
            audit.save_json(job_id, "01_textract_raw", response, filename=filename)

        text = self._extract_text_from_blocks(response['Blocks'])
        logger.info("Textract Sync completed.")
        
        return {
            "text": text,
            "blocks": response['Blocks'],
            "pages": response['DocumentMetadata']['Pages']
        }
        
    def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """Parses Blocks to return a clean string."""
        lines = []
        for block in blocks:
            if block['BlockType'] == 'LINE':
                lines.append(block['Text'])
        return "\n".join(lines)

textract_service = TextractService()
