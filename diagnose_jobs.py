import os
import sys
from sqlalchemy.orm import Session

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.database import SessionLocal, init_db
from app.db.models import Job, EmailContext

def diagnose():
    db = SessionLocal()
    try:
        # 1. Verificar total de jobs no SQLite
        total_jobs = db.query(Job).count()
        print(f"Total de Jobs no Banco de Dados SQLite: {total_jobs}")
        
        # Listar os status dos jobs existentes
        from sqlalchemy import func
        status_counts = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
        print("\nStatus dos Jobs:")
        for status, count in status_counts:
            print(f"- {status}: {count}")

        # Listar alguns message_ids
        print("\nAlguns message_ids e seus jobs:")
        sample_jobs = db.query(Job).limit(10).all()
        for j in sample_jobs:
            print(f"- Job ID: {j.id}, Message ID: {j.message_id}, Subject: {j.subject}, Status: {j.status}")

        # 2. Simular a chamada ao endpoint /grouped
        print("\n--- Simulando endpoint /grouped ---")
        from app.api.v1.endpoints.jobs import list_grouped_jobs
        
        # Testar chamada sem filtros
        res = list_grouped_jobs(db=db)
        print(f"Retorno do endpoint agrupado (sem filtros): {len(res)} emails retornados.")
        if len(res) > 0:
            print("Primeiro email agrupado retornado:")
            e = res[0]
            print(f"  Message ID: {e['message_id']}")
            print(f"  Subject: {e['subject']}")
            print(f"  Jobs vinculados ({len(e['jobs'])}):")
            for j in e['jobs']:
                print(f"    - Job ID: {j.id}, Attachment: {j.attachment_name}, Status: {j.status}")
                
    except Exception as e:
        print(f"Erro no diagnostico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
