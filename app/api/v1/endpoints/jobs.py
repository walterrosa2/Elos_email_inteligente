from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db.database import get_db
from app.db.models import Job, EmailContext
from app.api.schemas import schemas
from app.api.security import get_current_active_user, get_admin_user
from sqlalchemy import or_, desc
from app.db.models import SystemSetting
from app.storage.local_adapter import storage

from email.header import decode_header
import mimetypes

from loguru import logger
from app.classify.service import classification_service
from app.contracts.manager import contract_manager
from app.extract.service import extraction_service
from app.validation.service import validation_service

def decode_mime(text):
    if not text: return text
    if not isinstance(text, str): return str(text)
    try:
        if "=?" not in text: return text
        decoded_parts = decode_header(text)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                result += str(part)
        return result
    except:
        return text

router = APIRouter()

@router.get("", response_model=schemas.PaginatedResponse)
def list_jobs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    sender: Optional[str] = None,
    subject: Optional[str] = None,
    filename: Optional[str] = None,
    doc_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    criticality: Optional[str] = None,
    current_user=Depends(get_current_active_user)
):
    query = db.query(Job, EmailContext.criticality_score).outerjoin(
        EmailContext, Job.message_id == EmailContext.message_id
    )
    
    # Filtros Avançados
    if status_filter:
        if status_filter == "Concluído":
            # Processado com sucesso segundo um contrato
            query = query.filter(Job.status.in_(["EXTRACTED", "VALIDATED", "COMPLETED", "APPROVED", "REVIEW_PENDING", "EXPORTED"]))
            query = query.filter(Job.doc_type.isnot(None), Job.doc_type != "UNKNOWN", Job.doc_type != "unknown")
        elif status_filter == "Não mapeado":
            # Sem contrato ou marcado explicitamente como UNKNOWN, mas já processou
            query = query.filter(Job.status.not_in(["STAGED", "TEXT_EXTRACTED", "CLASSIFYING", "EXTRACTING"]))
            query = query.filter(or_(
                Job.status == "UNKNOWN_DOC_TYPE", 
                Job.doc_type == "UNKNOWN", 
                Job.doc_type == "unknown",
                Job.doc_type.is_(None)
            ))
        elif status_filter == "Pendente":
            query = query.filter(Job.status.in_(["STAGED", "TEXT_EXTRACTED", "CLASSIFYING", "EXTRACTING"]))
        elif status_filter == "Erro":
            query = query.filter(Job.status.in_(["ERROR", "FAILED"]))
        else:
            query = query.filter(Job.status == status_filter)

    if sender:
        query = query.filter(Job.sender.ilike(f"%{sender}%"))
    if subject:
        query = query.filter(Job.subject.ilike(f"%{subject}%"))
    if filename:
        query = query.filter(Job.attachment_name.ilike(f"%{filename}%"))
    if doc_type:
        query = query.filter(Job.doc_type.ilike(f"%{doc_type}%"))
    if start_date:
        query = query.filter(Job.received_at >= start_date)
    if end_date:
        from datetime import time
        end_of_day = datetime.combine(end_date.date(), time(23, 59, 59, 999999))
        query = query.filter(Job.received_at <= end_of_day)
    if criticality:
        query = query.filter(EmailContext.criticality_score == criticality)

    # Ordenação (Decrescente por received_at)
    query = query.order_by(desc(Job.received_at))

    total = query.count()
    jobs_data = query.offset(skip).limit(limit).all()

    # Modelagem para a view simplificada
    job_summaries = []
    for j, crit in jobs_data:
        if j.status in ["ERROR", "FAILED"]:
            sim_status = "Erro"
        elif j.status in ["STAGED", "TEXT_EXTRACTED", "CLASSIFYING", "EXTRACTING"]:
            sim_status = "Pendente"
        elif j.status == "UNKNOWN_DOC_TYPE" or j.doc_type in ["UNKNOWN", "unknown", None]:
            sim_status = "Não mapeado"
        else:
            # Se não é erro nem desconhecido, e tem um doc_type, consideramos concluído
            sim_status = "Concluído"

        job_summaries.append(
            schemas.JobSummary(
                id=j.id,
                status=j.status,
                simplified_status=sim_status,
                sender=decode_mime(j.sender),
                subject=decode_mime(j.subject),
                attachment_name=j.attachment_name,
                received_at=j.received_at,
                doc_type=j.doc_type,
                confidence=j.confidence,
                criticality=crit,
                extraction_result=j.extraction_result
            )
        )

    return schemas.PaginatedResponse(
        items=job_summaries,
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{job_id}", response_model=schemas.JobResponse)
def get_job_detail(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")
    
    # Decode fields for display
    job.sender = decode_mime(job.sender)
    job.subject = decode_mime(job.subject)
    return job

@router.get("/{job_id}/email", response_model=schemas.EmailContextResponse)
def get_job_email_context(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")
         
    email = db.query(EmailContext).filter(EmailContext.message_id == job.message_id).first()
    
    if not email:
         return {
             "message_id": job.message_id or "N/A",
             "body_text": "[No readable body found]", 
             "subject": decode_mime(job.subject), 
             "sender": decode_mime(job.sender),
             "received_at": job.received_at
         }
    
    # Ensure fields are decoded
    email_data = {
        "message_id": email.message_id,
        "body_text": email.body_text,
        "subject": decode_mime(email.subject or job.subject),
        "sender": decode_mime(email.sender or job.sender),
        "received_at": email.received_at,
        "tone": email.tone,
        "summary": email.summary,
        "criticality_score": email.criticality_score,
        "action_required": email.action_required
    }
    return email_data

@router.get("/{job_id}/file")
def get_job_file(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or not job.storage_uri:
        raise HTTPException(status_code=404, detail="File not found")
    
    path = storage.resolve_path(job.storage_uri)
    if not path or not path.exists():
        logger.error(f"File not found: {job.storage_uri} (resolved to {path})")
        raise HTTPException(status_code=404, detail=f"File not found on disk: {job.storage_uri}")
    
    media_type, _ = mimetypes.guess_type(str(path))
    if str(path).lower().endswith('.pdf'):
        media_type = "application/pdf"
    else:
        # Fallback para magic bytes caso não tenha extensão
        try:
            with open(path, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    media_type = "application/pdf"
        except Exception as e:
            logger.warning(f"Could not read magic bytes for {path}: {e}")
            
    return FileResponse(
        str(path), 
        media_type=media_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{job.attachment_name}"'}
    )


@router.patch("/{job_id}/extraction", response_model=schemas.JobResponse)
def update_job_extraction(
    job_id: int,
    request: schemas.JobUpdateExtraction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.extraction_result = request.extraction_result
    job.status = "VALIDATED" # Marcamos como validado após edição manual
    db.commit()
    return job

@router.post("/{job_id}/reprocess", response_model=schemas.JobResponse)
def reprocess_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Reprocessa um documento (email/anexo), executando novamente a classificação e extração,
    dado que ele pode ter sido categorizado como não mapeado e o gestor ajustou os contratos.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    logger.info(f"Reprocess Job {job_id}: textract_result type is {type(job.textract_result)}")
    if isinstance(job.textract_result, dict):
        logger.info(f"Reprocess Job {job_id}: keys are {job.textract_result.keys()}")

    # Somente prossegue se tiver o textract executado (idealmente, "TEXT_EXTRACTED" ou falhou classificação depois)
    tr = job.textract_result
    if not tr:
        raise HTTPException(status_code=400, detail="Texto não extraído pelo Textract. Impossível reprocessar sem o OCR original.")
    
    if isinstance(tr, str):
        import json
        try:
            tr = json.loads(tr)
        except Exception:
            pass

    if isinstance(tr, dict) and "text" not in tr:
        raise HTTPException(status_code=400, detail="Texto não extraído pelo Textract. Impossível reprocessar sem o OCR original.")

    text = tr.get("text", "") if isinstance(tr, dict) else str(tr)
    fname = job.attachment_name or ""
    
    # 1. Classification
    try:
        doc_type, confidence, reasoning = classification_service.classify_document(text, job_id=job.id, filename=fname)
        
        job.doc_type = doc_type
        job.confidence = confidence
        job.status = "CLASSIFIED"
        job.extraction_result = None
        job.validation_errors = None
        
        db.commit()
    except Exception as e:
        logger.error(f"Classification failed during reprocess for Job {job.id}: {e}")
        job.status = "FAILED"
        job.validation_errors = [str(e)]
        db.commit()
        return job

    # 2. Extraction & Validation (if classified successfully)
    try:
        contract = contract_manager.get_contract(job.doc_type)
        if not contract:
            logger.warning(f"No contract found for type '{job.doc_type}'. Using generic fallback.")
            from app.db.models import SystemSetting
            from app.contracts.manager import Contract as PydanticContract
            setting = db.query(SystemSetting).filter(SystemSetting.key == "openai_prompt_padrao").first()
            base_prompt = setting.value if setting else "Extraia as principais informações pertinentes deste documento em formato JSON."
            
            contract = PydanticContract(
                doc_type="UNKNOWN",
                version="1.0",
                description="Fallback Dinâmico",
                system_prompt=base_prompt,
                fields=[]
            )
            job.validation_errors = ["Contrato não encontrado. Usando extração base."]
            job.status = "UNKNOWN_DOC_TYPE"

        # Chamada ao GPT
        data = extraction_service.extract_data(text, contract, job_id=job.id, filename=fname)
        job.extraction_result = data
        job.status = "EXTRACTED"
        db.commit()

        # Validação do Contrato
        val_result = validation_service.validate(data, contract)
        if val_result["is_valid"]:
            job.status = "VALIDATED"
            if job.confidence and job.confidence > 0.9 and contract.doc_type != "UNKNOWN":
                job.status = "APPROVED"
            else:
                job.status = "REVIEW_PENDING"
        else:
            job.status = "REVIEW_PENDING"
            job.validation_errors = val_result["errors"]
        
        db.commit()
    except Exception as e:
        logger.error(f"Extraction failed during reprocess for Job {job.id}: {e}")
        job.status = "FAILED"
        if not job.validation_errors:
            job.validation_errors = []
        job.validation_errors.append(str(e))
        db.commit()

    return job

@router.post("/bulk-approve", response_model=schemas.MessageResponse)
def bulk_approve_jobs(
    request: schemas.JobBulkApprove,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Aprova múltiplos jobs de uma vez."""
    db.query(Job).filter(Job.id.in_(request.ids)).update(
        {"status": "APPROVED"}, synchronize_session=False
    )
    db.commit()
    return schemas.MessageResponse(message=f"{len(request.ids)} jobs aprovados com sucesso.")

@router.get("/stats/dashboard", response_model=schemas.JobStats)
def get_job_stats(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    """Retorna estatísticas detalhadas para o dashboard de auditoria."""
    from sqlalchemy import func
    
    # Status Distribution
    status_counts = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    status_dist = [schemas.JobStatItem(label=s, count=c) for s, c in status_counts]
    
    # Doc Type Distribution
    type_counts = db.query(Job.doc_type, func.count(Job.id)).filter(Job.doc_type.isnot(None)).group_by(Job.doc_type).all()
    type_dist = [schemas.JobStatItem(label=decode_mime(t) or "Não Mapeado", count=c) for t, c in type_counts]
    
    # Daily Volume (Last 30 days)
    # Simple grouping by date (SQLite specific cast if needed, but here generic-ish)
    daily_counts = db.query(func.date(Job.created_at), func.count(Job.id)).group_by(func.date(Job.created_at)).order_by(func.date(Job.created_at)).limit(30).all()
    daily_dist = [schemas.JobStatItem(label=str(d), count=c) for d, c in daily_counts]
    
    return schemas.JobStats(
        status_distribution=status_dist,
        doc_type_distribution=type_dist,
        daily_volume=daily_dist
    )

@router.get("/schedule/config", response_model=schemas.ScheduleConfig)
def get_schedule_config(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "ingestion_schedule").first()
    if not setting:
        return schemas.ScheduleConfig() # Default
    return setting.value

@router.post("/schedule/config", response_model=schemas.MessageResponse)
def save_schedule_config(
    config: schemas.ScheduleConfig,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user) # Apenas admin
):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "ingestion_schedule").first()
    if not setting:
        setting = SystemSetting(key="ingestion_schedule", value=config.model_dump(), description="Configuração do Agendador de Ingestão")
        db.add(setting)
    else:
        setting.value = config.model_dump()
    
    db.commit()
    return schemas.MessageResponse(message="Configuração de agendamento salva com sucesso.")
