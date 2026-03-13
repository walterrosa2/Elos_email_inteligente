@echo off
REM ============================================================
REM  _start.bat — Inicialização da App (Windows CMD)
REM  ELOS Pipeline V2 - Migração UI React + FastAPI
REM ============================================================

set BACKEND_PORT=8000
set FRONTEND_PORT=5173
set VENV_DIR=.venv
set PYTHONPATH=.

echo ========================================
echo   ELOS Pipeline V2 — Startup (SPA)
echo ========================================

REM 1. Detectar Python
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py -3
    goto :python_ok
)
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    goto :python_ok
)
echo [ERRO] Python nao encontrado.
pause
exit /b 1

:python_ok

REM 2. Ambiente
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Criando venv...
    %PYTHON_CMD% -m venv %VENV_DIR%
)
call "%VENV_DIR%\Scripts\activate.bat"

REM 2.1 Instalar dependencias Python (ANTES de subir os servicos)
echo [INFO] Verificando dependencias Python...
pip install -r requirements.txt --quiet

REM 3. Iniciar Backend em nova janela (apenas observando a pasta 'app')
echo [START] Iniciando Backend FastAPI...
start "ELOS Backend" cmd /k "set PYTHONPATH=. && .venv\Scripts\python.exe -m uvicorn app.api.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload --reload-dir app"

REM 4. Iniciar Frontend
if exist "frontend" (
    echo [START] Iniciando Frontend Vite...
    cd frontend
    if not exist "node_modules" (
        echo [INFO] Instalando dependencias Node...
        call npm install --quiet
    )
    call npm run dev -- --port %FRONTEND_PORT%
    cd ..
) else (
    echo [ERRO] Pasta 'frontend' nao encontrada.
)

pause
