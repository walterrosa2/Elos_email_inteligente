<# ============================================================
#  _start.ps1 — Inicialização da App (Windows PowerShell)
#  ELOS Pipeline V2 - Migração UI React + FastAPI
# ============================================================ #>

$ErrorActionPreference = "Continue"

$BACKEND_PORT = 8000
$FRONTEND_PORT = 5173
$VENV_DIR     = ".venv"
$PYTHON_PATH  = "."

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ELOS Pipeline V2 — Startup (SPA)     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Detectar Python
$pythonCmd = $null
if (Get-Command "py" -ErrorAction SilentlyContinue) { $pythonCmd = "py -3" }
elseif (Get-Command "python" -ErrorAction SilentlyContinue) { $pythonCmd = "python" }
else { 
    Write-Host "[ERRO] Python não encontrado." -ForegroundColor Red
    exit 1 
}

# 2. Ativar Ambiente
if (-Not (Test-Path "$VENV_DIR\Scripts\activate.ps1")) {
    Write-Host "[INFO] Criando venv..." -ForegroundColor Yellow
    Invoke-Expression "$pythonCmd -m venv $VENV_DIR"
}
& "$VENV_DIR\Scripts\activate.ps1"

# 2.1 Instalar dependências Python (ANTES de subir os serviços)
Write-Host "[INFO] Verificando dependências Python..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# 3. Validar .env
if (-Not (Test-Path ".env")) {
    Write-Host "[AVISO] Arquivo .env não encontrado. Copiando do .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 4. Iniciar Backend (Nova Janela para melhor debug)
Write-Host "[START] Iniciando Backend FastAPI em http://localhost:$BACKEND_PORT ..." -ForegroundColor Green
$env:PYTHONPATH = $PYTHON_PATH
# Usamos o executável direto da venv para evitar conflitos de path
Start-Process "cmd.exe" -ArgumentList "/k `".venv\Scripts\python.exe -m uvicorn app.api.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload --reload-dir app`""

# 5. Iniciar Frontend (Vite)
if (Test-Path "frontend") {
    Write-Host "[START] Iniciando Frontend Vite..." -ForegroundColor Green
    Set-Location frontend
    if (-Not (Test-Path "node_modules")) {
        Write-Host "[INFO] Instalando dependências Node (pode demorar)..." -ForegroundColor Yellow
        npm install --quiet
    }
    # Executar dev server
    npm run dev -- --port $FRONTEND_PORT
    Set-Location ..
} else {
    Write-Host "[ERRO] Pasta 'frontend' não encontrada." -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Aplicação Encerrada.                 " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
