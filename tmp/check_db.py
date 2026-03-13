from app.db.database import SessionLocal
from app.db.models import Job
import json

def check_db():
    db = SessionLocal()
    try:
        jobs = db.query(Job).limit(20).all()
        print(f"Found {len(jobs)} jobs.")
        for job in jobs:
            print(f"ID: {job.id}, Status: {job.status}, DocType: {job.doc_type}")
            print(f"Extraction Result: {json.dumps(job.extraction_result, indent=2)}")
            print("-" * 20)
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
