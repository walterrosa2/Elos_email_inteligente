import logging
from app.db.database import SessionLocal
from app.db.models import Job
from app.orchestrator.pipeline import PipelineOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)

db = SessionLocal()
job = db.query(Job).filter(Job.id == 594).first()
if job:
    print("Found job 594:", job.subject, job.status)
    # Reset status to STAGED
    job.status = "STAGED"
    db.commit()

# Monkey patch PipelineOrchestrator to only run on this job
p = PipelineOrchestrator(db)
# Override staged_jobs
staged_jobs = db.query(Job).filter(Job.id == 594).all()

# Instead of rewriting pipeline, I'll just run it with limit 1
print("Executing pipeline...")
p.run_pipeline()

# After pipeline
job = db.query(Job).filter(Job.id == 594).first()
print("Final Status:", job.status)
print("Doc Type:", job.doc_type)
print("Validation Errors:", job.validation_errors)
print("Extraction Result:", job.extraction_result)
