from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from app.core.config import settings
from app.email_client.imap_service import IMAPService
from app.ingest.staging import StagingService
from app.ingest.pdf_check import PDFCheck
from app.ingest.ocr import OCRProcessor
from app.ingest.nf_classifier import NFClassifier
from app.extract.nfe_danfe import NFeExtractor
from app.extract.nfse import NFSeExtractor
from app.outputs.excel_writer import ExcelReportWriter
from app.outputs.json_writer import JSONWriter
from app.core.models import Erro

class Pipeline:
    def __init__(self):
        self.imap = IMAPService()
        self.staging = StagingService()
        self.ocr = OCRProcessor()
        self.classifier = NFClassifier()
        self.nfe_ext = NFeExtractor()
        self.nfse_ext = NFSeExtractor()
        self.json_writer = JSONWriter()
        
    def run(self, days_back: int = 1, password: str = None):
        """
        Executes the main pipeline:
        Fetch -> Stage -> OCR -> Classify -> Extract -> Save
        """
        logger.info(f"Starting pipeline run. Scan window: {days_back} days.")
        
        # 1. Connect
        if not password:
            # Try to get from keyring or env var fallback
            import os
            password = os.getenv("EMAIL_PASSWORD")
            if not password:
                import keyring
                password = keyring.get_password(settings.KEYRING_SERVICE_NAME, settings.EMAIL_USER)
            
            if not password:
                logger.error("Password not found in Env or Keyring.")
                return

        self.imap.connect(password)

        if password:
             masked_pass = password[:2] + "****" + password[-2:] if len(password) > 4 else "****"
             logger.info(f"Pipeline connecting with password: {masked_pass} (Length: {len(password)})")

        
        # 2. Search
        since_date = datetime.now().date() - timedelta(days=days_back)
        msg_ids = self.imap.search_candidates(since_date=since_date)
        
        for mid in msg_ids:
            try:
                msg_data = self.imap.fetch_message_data(mid)
                if not msg_data: continue
                
                email_obj = msg_data['email_object']
                msg_dt_str = msg_data.get('date')
                # date parsing logic same as staging...
                
                # 3. Stage (Download)
                saved_paths = self.staging.process_message(email_obj, mid)
                
                if not saved_paths:
                    continue
                
                # Prepare batch lists
                batch_cabs = []
                batch_items = []
                batch_erros = []
                # For MVP Staging saves Origem JSONs. We could reload them if we want to put in Excel.
                # Let's simplify: Staging handles Origem persistence. Excel needs it too. 
                # Ideally Staging returns the Origem objects too.
                # Refactoring Staging to return objects would be cleaner, but for now let's focus on Extraction.
                
                # 4. Process Attachments
                for pdf_path in saved_paths:
                    self.process_file(pdf_path, str(mid), msg_dt_str, batch_cabs, batch_items, batch_erros)
                
                # 5. Write Batch to Excel
                # Determine Excel Path (Daily)
                # Using date from first file or today? Use folder structure date.
                if saved_paths:
                     dt_folder = saved_paths[0].parent.parent # .../DD
                     excel_path = dt_folder / "planilhas" / f"Relatorio_{dt_folder.name}_{dt_folder.parent.name}.xlsx"
                     writer = ExcelReportWriter(excel_path)
                     writer.write_batch(batch_cabs, batch_items, batch_erros, []) 
                     # Note: Origem not passed here if not refactored. 
                     # Future improvement: Staging returns Origem objects.

            except Exception as e:
                logger.exception(f"Error processing message {mid}: {e}")
        
        self.imap.disconnect()
        logger.info("Pipeline run finished.")

    def process_file(self, input_path: Path, msg_id: str, dt_email_str, cabs: list, items: list, erros: list):
        logger.info(f"Processing file: {input_path.name}")
        
        # Check Validity
        if not PDFCheck.is_valid(input_path):
            erros.append(Erro(dt_email=datetime.now(), msg_id=msg_id, arquivo=input_path.name, motivo="Arquivo Inválido/Corrompido"))
            return

        # Check Text / OCR
        work_path = input_path # default
        if not PDFCheck.has_text(input_path):
             # Define processados path
             proc_path = input_path.parent.parent / "processados" / input_path.name
             if self.ocr.ensure_searchable(input_path, proc_path):
                 work_path = proc_path
             else:
                 erros.append(Erro(dt_email=datetime.now(), msg_id=msg_id, arquivo=input_path.name, motivo="Falha OCR", action_sugerida="Verificar log"))
                 # proceed with original or abort? Abort extraction if no text.
                 if not PDFCheck.has_text(work_path): 
                    return

        # Extract Text
        from pdfminer.high_level import extract_text
        text = extract_text(str(work_path))
        
        # Classify
        tipo = self.classifier.classify(text)
        logger.info(f"Classified {input_path.name} as {tipo}")
        
        try:
            cab = None
            extracted_items = []
            
            # Context Date
            from app.extract.common import TextNormalizer
            dt_ctx = TextNormalizer.parse_date(dt_email_str) or datetime.now() # naive approach

            if tipo == "NFE" or tipo == "CTE":
                 cab, extracted_items = self.nfe_ext.extract(text, msg_id, dt_ctx)
            elif tipo == "NFSE":
                 cab, extracted_items = self.nfse_ext.extract(text, msg_id, dt_ctx)
            else:
                 erros.append(Erro(dt_email=dt_ctx, msg_id=msg_id, arquivo=input_path.name, motivo="Tipo Desconhecido/Não Suportado", detalhe=tipo))
                 return

            if cab:
                # Add filename context if missing
                # cab.arquivo = input_path.name # (Model doesn't have arquivo in Cabecalho but maybe should?)
                # Validation
                # (Assuming Validator usage)
                pass 
                
            if cab: cabs.append(cab)
            if extracted_items: items.extend(extracted_items)
            
            # Save JSON
            json_path = input_path.parent.parent / "json" / f"{input_path.stem}.json"
            if cab: self.json_writer.save_invoice(cab, extracted_items, json_path)

        except Exception as e:
            logger.exception(f"Extraction failed for {input_path.name}: {e}")
            erros.append(Erro(dt_email=datetime.now(), msg_id=msg_id, arquivo=input_path.name, motivo="Erro Extração", detalhe=str(e)))
