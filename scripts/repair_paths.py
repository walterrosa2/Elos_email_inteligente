from pathlib import Path
from app.db.database import SessionLocal
from app.db.models import Job
from app.core.logging import logger

def repair_storage_paths():
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.status == "STAGED").all()
        logger.info(f"Checking {len(jobs)} jobs for path repair...")
        
        # Base project path from current file location (app/../..)
        project_root = Path(__file__).parent.parent.parent.absolute()
        
        fixed_count = 0
        for job in jobs:
            if not job.storage_uri: continue
            
            p = Path(job.storage_uri)
            if not p.exists():
                # Try to see if it was truncated but exists in the default storage location
                # Expected pattern: dados/storage/YYYY/MM/DD/filename
                # Truncation usually happens at 'dados' or elsewhere.
                
                # Check if we can find the filename in the storage directories
                storage_base = project_root / "dados" / "storage"
                filename = job.attachment_name
                
                logger.warning(f"File not found: {job.storage_uri}. Searching in {storage_base} for {filename}...")
                
                # Recursive search for the filename
                found = list(storage_base.glob(f"**/{filename}"))
                if found:
                    new_path = str(found[0].absolute())
                    logger.info(f"Fixed Job {job.id}: {new_path}")
                    job.storage_uri = new_path
                    fixed_count += 1
                else:
                    logger.error(f"Could not find file for Job {job.id}: {filename}")
        
        if fixed_count > 0:
            db.commit()
            logger.info(f"Repaired {fixed_count} job paths.")
        else:
            logger.info("No paths needed repair or could be fixed.")
            
    finally:
        db.close()

if __name__ == "__main__":
    repair_storage_paths()
