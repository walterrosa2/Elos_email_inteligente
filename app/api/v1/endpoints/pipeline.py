from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.db.database import get_db, SessionLocal
from app.api.security import get_current_active_user
from app.db.models import User
from pydantic import BaseModel
import traceback

from app.ingest.service import IngestionService
from app.orchestrator.pipeline import PipelineOrchestrator

router = APIRouter()

class IngestRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ProcessRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class PipelineResponse(BaseModel):
    message: str
    status: str

# Async wrappers to not block the API
def run_ingestion_task(start: Optional[date], end: Optional[date]):
    db = SessionLocal()
    try:
        # Se as datas nao foram fornecidas (ex: scheduler diário automático), 
        # forcar uma janela dos ultimos 3 dias para nao travar o Office365 baixando mailbox inteira
        import datetime
        if not start and not end:
            end = datetime.date.today()
            start = end - datetime.timedelta(days=3)
            
        ingestor = IngestionService(db)
        ingestor.process_new_emails(start_date=start, end_date=end)
    except Exception as e:
        print(f"Error in background ingestion: {e}")
        traceback.print_exc()
    finally:
        db.close()

def run_extraction_task(start: Optional[date] = None, end: Optional[date] = None):
    db = SessionLocal()
    try:
        orch = PipelineOrchestrator(db)
        orch.run_pipeline(start_date=start, end_date=end)
    except Exception as e:
        print(f"Error in background pipeline: {e}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/ingest", response_model=PipelineResponse)
def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Dispara a busca de e-mails via IMAP em background
    """
    # Importante instanciar sessoes DB separadas pro background depois se o SQLAlchemy reclamar,
    # agora o BD ja opera com Sessao dedicada dentro da task.
    background_tasks.add_task(run_ingestion_task, request.start_date, request.end_date)
    return PipelineResponse(message="Ingestão iniciada em background.", status="processing")

@router.post("/process", response_model=PipelineResponse)
def trigger_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Dispara OCR e Extração LLM na fila de jobs atual
    """
    background_tasks.add_task(run_extraction_task, request.start_date, request.end_date)
    return PipelineResponse(message="Processamento (OCR/LLM) iniciado em background.", status="processing")
