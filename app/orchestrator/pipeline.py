from sqlalchemy.orm import Session
from app.db.models import Job
from app.core.logging import logger
from app.storage.local_adapter import storage
from app.textract.service import textract_service
from app.classify.service import classification_service
from app.contracts.manager import contract_manager
from app.extract.service import extraction_service
from app.validation.service import validation_service

class PipelineOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def run_pipeline(self, start_date=None, end_date=None):
        """
        Runs the full pipeline for Jobs in specific states.
        STAGED -> TEXT_EXTRACTED -> CLASSIFIED -> EXTRACTED -> VALIDATED -> REVIEW
        """
        logger.info(f"Starting pipeline execution cycle... Filter: {start_date} to {end_date}")
        
        # Base query filter for dates
        import datetime
        def apply_date_filter(query):
            if start_date:
                # Se for objeto date (sem hora), garantir inicio do dia
                d_start = start_date
                if not hasattr(d_start, 'hour'):
                    d_start = datetime.datetime.combine(d_start, datetime.time.min)
                query = query.filter(Job.received_at >= d_start)
            if end_date:
                # Se for objeto date (sem hora), garantir fim do dia (23:59:59)
                d_end = end_date
                if not hasattr(d_end, 'hour'):
                    d_end = datetime.datetime.combine(d_end, datetime.time.max)
                query = query.filter(Job.received_at <= d_end)
            return query

        # Limit per step
        limit = 50

        # 1. Textract (Target: STAGED jobs)
        query = self.db.query(Job).filter(Job.status == "STAGED")
        query = apply_date_filter(query)
        staged_jobs = query.limit(limit).all()

        for job in staged_jobs:
            try:
                logger.info(f"Processing Textract for Job {job.id}")
                file_bytes = storage.get_file(job.storage_uri)
                
                fname = job.attachment_name.lower() if job.attachment_name else ""
                result = {}

                if fname.endswith(".pdf"):
                    # Use multipage strategy (Split-and-Sync)
                    result = textract_service.process_document_multipage(file_bytes, job_id=job.id, filename=job.attachment_name)
                
                elif fname.endswith((".txt", ".xml", ".json", ".csv", ".html", ".md", ".log", ".xlsx", ".xls", ".zip", ".rar")):
                    # Read text directly or set metadata for non-OCR files
                    msg_text = f"File Type: {fname.split('.')[-1].upper()}\n"
                    
                    try:
                        if fname.endswith((".txt", ".xml", ".json", ".csv", ".html", ".md", ".log")):
                            def robust_decode(data):
                                for enc in ['utf-8', 'iso-8859-1', 'windows-1252', 'latin-1']:
                                    try:
                                        return data.decode(enc)
                                    except:
                                        continue
                                return data.decode('utf-8', errors='replace')
                            
                            content = robust_decode(file_bytes)
                            msg_text += content
                        elif fname.endswith((".xlsx", ".xls")):
                            try:
                                import pandas as pd
                                import io
                                df = pd.read_excel(io.BytesIO(file_bytes))
                                msg_text += df.to_string()
                            except Exception as e:
                                msg_text += f" [Error reading Excel content: {str(e)}]"

                        elif fname.endswith((".zip", ".rar")):
                            msg_text += " [Compressed Archive - Content not extracted automatically]"
                    except Exception as e:
                         msg_text += f" [Error reading file content: {str(e)}]"

                    result = {"text": msg_text, "pages": 1}
                    logger.info(f"Job {job.id}: Text/Data prepared for {fname} (Skipped Textract).")
                    
                else:
                    logger.warning(f"Job {job.id}: File type {fname} not supported for auto-OCR. Moving to Review.")
                    job.status = "REVIEW_PENDING"
                    job.validation_errors = ["Tipo de arquivo não suportado para OCR automático"]
                    self.db.commit()
                    continue

                # Store text
                job.textract_result = result
                job.status = "TEXT_EXTRACTED"
                self.db.commit()
            except Exception as e:
                logger.error(f"Textract failed for Job {job.id}: {e}")
                job.status = "FAILED"
                job.validation_errors = [str(e)]
                self.db.commit()

        # 2. Classification (Target: TEXT_EXTRACTED)
        query = self.db.query(Job).filter(Job.status == "TEXT_EXTRACTED")
        query = apply_date_filter(query)
        class_jobs = query.limit(limit).all()
        
        for job in class_jobs:
            try:
                text = job.textract_result.get("text", "")
                doc_type, confidence, reasoning = classification_service.classify_document(text, job_id=job.id, filename=job.attachment_name)
                
                job.doc_type = doc_type
                job.confidence = confidence
                
                job.status = "CLASSIFIED"
                self.db.commit()
            except Exception as e:
                logger.error(f"Classification failed for Job {job.id}: {e}")
                job.status = "FAILED"
                job.validation_errors = [str(e)]
                self.db.commit()

        # 3. Extraction & Validation (Target: CLASSIFIED)
        query = self.db.query(Job).filter(Job.status == "CLASSIFIED")
        query = apply_date_filter(query)
        extract_jobs = query.limit(limit).all()

        for job in extract_jobs:
            try:
                contract = contract_manager.get_contract(job.doc_type)
                
                if not contract:
                    logger.warning(f"No contract found for type '{job.doc_type}'. Using generic fallback extraction.")
                    from app.db.models import SystemSetting
                    from app.contracts.manager import Contract as PydanticContract # alias if needed
                    setting = self.db.query(SystemSetting).filter(SystemSetting.key == "openai_prompt_padrao").first()
                    base_prompt = setting.value if setting else "Extraia as principais informações pertinentes deste documento (faturas, valores, datas, nomes) em um formato JSON chave-valor."
                    
                    contract = PydanticContract(
                        doc_type="GENERIC_FALLBACK",
                        version="1.0",
                        description="Fallback Dinâmico",
                        system_prompt=base_prompt,
                        fields=[]
                    )
                    job.validation_errors = ["Contract was generated dynamically as fallback"]

                text = job.textract_result.get("text", "")
                data = extraction_service.extract_data(text, contract, job_id=job.id, filename=job.attachment_name)
                
                # --- Lógica de Vencimento Inteligente (V4.0) ---
                due_date_anexo = data.pop("_vencimento_data", None)
                due_context_anexo = data.pop("_vencimento_trecho", None)
                
                # Salvar vencimento específico do anexo
                job.original_due_date = due_date_anexo
                job.due_date_context = due_context_anexo
                job.extraction_result = data
                job.status = "EXTRACTED"
                self.db.commit()

                # Garantir que o email seja analisado de imediato para termos o vencimento do corpo
                from app.analysis.email_agent import EmailAnalysisService
                from app.db.models import EmailContext
                email_analyzer = EmailAnalysisService(self.db)
                ctx = self.db.query(EmailContext).filter(EmailContext.message_id == job.message_id).first()
                if ctx and ctx.criticality_score is None:
                    try:
                        email_analyzer._analyze_single_email(ctx)
                    except Exception as e:
                        logger.error(f"Erro ao analisar email do job {job.id} na extração: {e}")

                # Salvar vencimento do corpo do email no Job para facilidade de visualização
                if ctx:
                    job.email_body_due_date = ctx.detected_due_date

                # Decidir se tem vencimento ou não
                has_vencimento = False
                if due_date_anexo:
                    has_vencimento = True
                elif ctx and ctx.detected_due_date:
                    has_vencimento = True

                # Se não tem vencimento detectado, mover para a pasta "Sem Vencimento"
                if not has_vencimento:
                    try:
                        local_path = storage.resolve_path(job.storage_uri)
                        if local_path and local_path.exists():
                            import shutil
                            from pathlib import Path
                            sem_venc_dir = local_path.parent / "Sem Vencimento"
                            sem_venc_dir.mkdir(parents=True, exist_ok=True)
                            new_path = sem_venc_dir / local_path.name
                            
                            logger.info(f"Movendo arquivo sem vencimento de {local_path} para {new_path}")
                            shutil.move(str(local_path), str(new_path))
                            
                            # Atualizar storage_uri do Job para a nova localização
                            relative_new_path = Path(job.storage_uri).parent / "Sem Vencimento" / local_path.name
                            job.storage_uri = str(relative_new_path).replace("\\", "/")
                            self.db.commit()
                    except Exception as e:
                        logger.error(f"Erro ao mover arquivo sem vencimento para quarentena no Job {job.id}: {e}")
                
                # Validation (Immediately follow up)
                val_result = validation_service.validate(data, contract)
                
                if val_result["is_valid"]:
                    job.status = "VALIDATED"
                    if job.confidence > 0.9 and contract.doc_type != "GENERIC_FALLBACK": 
                        job.status = "APPROVED" 
                        logger.info(f"Registro {job.id} marcado como Concluído (APPROVED) com confiança {job.confidence}.")
                    else:
                         job.status = "REVIEW_PENDING"
                else:
                    job.status = "REVIEW_PENDING"
                    job.validation_errors = val_result["errors"]
                
                self.db.commit()

            except Exception as e:
                logger.error(f"Extraction/Validation failed for Job {job.id}: {e}")
                job.status = "FAILED"
                job.validation_errors = [str(e)]
                self.db.commit()

        # 4. Email Analysis (V3.0)
        try:
            from app.analysis.email_agent import EmailAnalysisService
            email_analyzer = EmailAnalysisService(self.db)
            
            # Preparar datas para o analyzer (EmailContext usa received_at)
            d_start = start_date
            if d_start and not hasattr(d_start, 'hour'):
                d_start = datetime.datetime.combine(d_start, datetime.time.min)
            d_end = end_date
            if d_end and not hasattr(d_end, 'hour'):
                d_end = datetime.datetime.combine(d_end, datetime.time.max)

            n_analyzed = email_analyzer.analyze_pending_contexts(start_date=d_start, end_date=d_end)
            if n_analyzed > 0:
                logger.info(f"Analyzed {n_analyzed} emails for criticality.")
        except Exception as e:
            logger.error(f"Email Analysis failed: {e}")

        logger.info("Pipeline cycle finished.")
