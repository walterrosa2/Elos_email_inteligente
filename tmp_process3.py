import logging
from app.db.database import SessionLocal
from app.db.models import Job
from app.orchestrator.pipeline import PipelineOrchestrator

logging.basicConfig(level=logging.INFO)
db = SessionLocal()

# Reset job 594 status to CLASSIFIED so pipeline can pick it up from CLASSIFIED step
job = db.query(Job).filter(Job.id == 594).first()
if job:
    job.status = "CLASSIFIED"
    job.extraction_result = None
    job.validation_errors = None
    db.commit()

p = PipelineOrchestrator(db)
# We mock out all DB queries for STAGED and CLASSIFIED because 
# run_pipeline queries limit 10. Let's patch it.

# Running extraction manually based on pipeline's logic
extract_jobs = db.query(Job).filter(Job.id == 594).all()
for job in extract_jobs:
    from app.contracts.manager import contract_manager
    from app.extract.service import extraction_service
    from app.db.models import SystemSetting
    from app.contracts.manager import Contract as PydanticContract
    
    contract = contract_manager.get_contract(job.doc_type)
    
    if not contract:
        print(f"No contract found for type '{job.doc_type}'. Using generic fallback extraction.")
        setting = db.query(SystemSetting).filter(SystemSetting.key == "openai_prompt_padrao").first()
        base_prompt = setting.value if setting else "Extraia as principais informações pertinentes deste documento (faturas, valores, datas, nomes) em um formato JSON chave-valor."
        
        contract = PydanticContract(
            doc_type="GENERIC_FALLBACK",
            version="1.0",
            description="Fallback Dinâmico",
            system_prompt=base_prompt,
            fields=[]
        )
        job.validation_errors = ["Contract was generated dynamically as fallback"]

    text = job.textract_result.get("text", "") if job.textract_result else ""
    data = extraction_service.extract_data(text, contract, job_id=job.id, filename=job.attachment_name)
    job.extraction_result = data
    print("EXTRACTED DATA: ", data)
    job.status = "EXTRACTED"
    db.commit()

