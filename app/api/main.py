from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.v1.endpoints import auth, jobs, pipeline, settings, contracts, reports
from app.scheduler import scheduler_manager

app = FastAPI(
    title="ELOS Pipeline V2 API",
    description="REST API para gerenciamento de Ingestão e Agendamento de Emails",
    version="2.0.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# 1. CORS Configuration (Specific origins required when allow_credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 2. Included Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["Contracts"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])

@app.on_event("startup")
async def startup_event():
    scheduler_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler_manager.shutdown()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.1"}

# 3. SPA Support
frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{rest_of_path:path}")
    async def serve_spa(rest_of_path: str):
        if rest_of_path.startswith("api/") or rest_of_path.startswith("docs"):
             from fastapi import HTTPException
             raise HTTPException(status_code=404, detail="API Route Not Found")
        return FileResponse(os.path.join(frontend_dist, "index.html"))
