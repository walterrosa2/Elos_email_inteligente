from app.db.database import SessionLocal
from app.db.models import Job
from app.contracts.manager import contract_manager
from app.extract.service import extraction_service
from app.validation.service import validation_service
from app.classify.service import classification_service
from app.textract.service import textract_service
from app.storage.local_adapter import storage
import logging

logging.basicConfig(level=logging.INFO)

db = SessionLocal()
job = db.query(Job).filter(Job.id == 594).first()
if not job:
    print("Job 594 not found")
    exit()

print("Job 594:", job.subject)

file_bytes = storage.get_file(job.storage_uri)
fname = job.attachment_name.lower() if job.attachment_name else ""

print("File name:", fname)

# Textract
if fname.endswith(".pdf"):
    print("Running Textract...")
    result = textract_service.process_document_multipage(file_bytes, job_id=job.id, filename=job.attachment_name)
    job.textract_result = result
    print("Textract Done.")

# Classification
text = job.textract_result.get("text", "") if job.textract_result else ""
doc_type, confidence, _ = classification_service.classify_document(text, job_id=job.id, filename=job.attachment_name)
print(f"Classified as: {doc_type} with confidence {confidence}")
job.doc_type = doc_type
job.confidence = confidence

# Extraction
contract = contract_manager.get_contract(job.doc_type)
if not contract:
    print(f"No contract found for type '{job.doc_type}'.")
else:
    print(f"Contract found: {contract.doc_type}")
    data = extraction_service.extract_data(text, contract, job_id=job.id, filename=job.attachment_name)
    job.extraction_result = data
    print("Extracted Data:", data)
    
    val_result = validation_service.validate(data, contract)
    print("Validation Result:", val_result)

db.close()
