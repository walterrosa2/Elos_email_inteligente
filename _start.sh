#!/usr/bin/env bash
# ============================================================
#  _start.sh — Inicialização da App (Linux / Docker / Railway)
#  Pipeline V2.1 - ELOS - Salvamento e tabulação de e-mails
# ============================================================

set -euo pipefail

APP_PORT="${APP_PORT:-8501}"
APP_HOST="${APP_HOST:-0.0.0.0}"
VENV_DIR=".venv"
REQ_FILE="requirements.txt"
ENTRY="streamlit_app.py"

echo "========================================"
echo "  ELOS Pipeline V2.1 — Startup (Linux) "
echo "========================================"

# --- 1. Verificar Python ---
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERRO] Python não encontrado. Instale o Python 3.10+."
    exit 1
fi
echo "[OK] Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"

# --- 2. Criar venv (se não existir e não estivermos em container) ---
if [ -z "${CONTAINER:-}" ]; then
    if [ ! -d "$VENV_DIR/bin" ]; then
        echo "[INFO] Criando venv em $VENV_DIR ..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    # --- 3. Activar venv ---
    echo "[INFO] Ativando venv ..."
    source "$VENV_DIR/bin/activate"
fi

# --- 4. Instalar dependências (idempotente) ---
if [ -f "$REQ_FILE" ]; then
    echo "[INFO] Instalando dependências ..."
    pip install -r "$REQ_FILE" --quiet
else
    echo "[AVISO] $REQ_FILE não encontrado. Pulando instalação."
fi

# --- 5. Verificar .env ---
if [ ! -f ".env" ] && [ -z "${CONTAINER:-}" ]; then
    echo "[AVISO] Arquivo .env não encontrado!"
    echo "        Copie .env.example para .env e preencha as variáveis."
fi

# --- 6. Iniciar Streamlit ---
echo ""
echo "[START] Iniciando Streamlit em http://${APP_HOST}:${APP_PORT}"
echo "        Pressione Ctrl+C para encerrar."
echo ""

$PYTHON_CMD -m streamlit run "$ENTRY" \
    --server.port "$APP_PORT" \
    --server.address "$APP_HOST" \
    --server.headless true
