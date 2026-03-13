from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db.database import SessionLocal
from app.db.models import SystemSetting
from app.api.v1.endpoints.pipeline import run_ingestion_task, run_extraction_task
from loguru import logger
import json

class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_session = SessionLocal()

    def start(self):
        """Inicia o agendador e carrega os jobs do banco de dados."""
        if self.scheduler.running:
            logger.warning("Scheduler already running.")
            return

        logger.info("Initializing Scheduler Manager...")
        self._load_jobs()
        self.scheduler.start()
        logger.info("Scheduler started successfully.")

    def shutdown(self):
        """Para o agendador."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down.")
        self.db_session.close()

    def _load_jobs(self):
        """Lê a configuração do banco e agenda as tarefas."""
        try:
            setting = self.db_session.query(SystemSetting).filter(SystemSetting.key == "ingestion_schedule").first()
            if not setting:
                logger.info("No ingestion schedule configuration found in database. Using defaults (disabled).")
                return

            config = setting.value
            # Se vier como string, converter pra dict
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except:
                    logger.error("Failed to parse ingestion_schedule JSON string.")
                    return

            enabled = config.get("enabled", False)
            interval_minutes = config.get("interval_minutes", 15)

            if enabled:
                logger.info(f"Scheduling ingestion and extraction every {interval_minutes} minutes.")
                
                # Job 1: Ingestão (Busca novos e-mails)
                self.scheduler.add_job(
                    run_ingestion_task,
                    IntervalTrigger(minutes=interval_minutes),
                    args=[None, None], # start_date, end_date (vai usar o default de 3 dias)
                    id="ingestion_job",
                    replace_existing=True
                )

                # Job 2: Extração (Processa a fila)
                # O ideal é rodar um pouco depois ou em paralelo. 
                # Aqui vamos rodar no mesmo intervalo, o orchestrator vai pegar o que tiver STAGED.
                self.scheduler.add_job(
                    run_extraction_task,
                    IntervalTrigger(minutes=interval_minutes),
                    args=[None, None],
                    id="extraction_job",
                    replace_existing=True
                )
            else:
                logger.info("Ingestion schedule is disabled in settings.")

        except Exception as e:
            logger.error(f"Error loading scheduler jobs: {e}")

    def reload(self):
        """Recarrega os jobs (útil se a configuração mudar em runtime)."""
        logger.info("Reloading scheduler jobs...")
        self.scheduler.remove_all_jobs()
        self._load_jobs()

# Singleton instance
scheduler_manager = SchedulerManager()
