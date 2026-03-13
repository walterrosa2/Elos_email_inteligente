import sys
from pathlib import Path

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from app.scheduler import scheduler_manager

import asyncio

async def smoke_test_scheduler():
    print("=== SMOKE TEST: Scheduler Manager ===")
    
    # 1. Verificar se o agendador inicializa sem erros
    try:
        # Força criação de um event loop se não existir
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        scheduler_manager.start()
        print("[OK] Scheduler started.")
        
        # 2. Listar jobs agendados
        jobs = scheduler_manager.scheduler.get_jobs()
        print(f"[INFO] Active jobs: {len(jobs)}")
        for job in jobs:
            print(f"  - Job ID: {job.id}, Next run: {job.next_run_time}, Trigger: {job.trigger}")
            
        # 3. Testar shutdown
        scheduler_manager.shutdown()
        print("[OK] Scheduler shut down.")
        
    except Exception as e:
        print(f"[ERROR] Smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(smoke_test_scheduler())
