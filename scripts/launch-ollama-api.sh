#!/usr/bin/env bash
set -e

# Production launch script for Samplemind Ollama API

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
APP_MODULE="src.samplemind.interfaces.api.ollama_api:app"
PORT=8000
WORKERS=$(python -c 'import os; print(os.cpu_count() or 2)')

if [ ! -d "$VENV_DIR" ]; then
  echo "[!] Python venv not found. Please run setup first."
  exit 1
fi

source "$VENV_DIR/bin/activate"

# Preload models by hitting the health endpoint (triggers FastAPI startup event)
echo "[+] Preloading models via FastAPI startup..."
curl -s http://localhost:$PORT/api/health || true

# Start the API
CMD="uvicorn $APP_MODULE --host 0.0.0.0 --port $PORT --workers $WORKERS"
echo "[+] Starting Ollama API: $CMD"
eval $CMD 