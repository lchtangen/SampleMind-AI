#!/usr/bin/env bash
set -e

# Setup script for Samplemind AI Python development with open-source LLMs

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
SAMPLE_FILE="src/samplemind/integrations/ollama_integration.py"

# 1. Create Python virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
  echo "[+] Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
else
  echo "[=] Python virtual environment already exists."
fi

# 2. Activate virtual environment
source "$VENV_DIR/bin/activate"

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install required packages
REQUIRED_PKGS=(requests langchain llama-index chromadb fastapi uvicorn)
echo "[+] Installing required Python packages: ${REQUIRED_PKGS[*]}..."
pip install "${REQUIRED_PKGS[@]}"

# 5. Create sample integration file if not exists
if [ ! -f "$SAMPLE_FILE" ]; then
  echo "[+] Creating sample Ollama integration file at $SAMPLE_FILE..."
  mkdir -p "$(dirname "$SAMPLE_FILE")"
  cat > "$SAMPLE_FILE" <<'EOF'
import requests

OLLAMA_URL = "http://localhost:11434"

def run_llm(prompt, model="llama3.1:8b-instruct"):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": model, "prompt": prompt}
    )
    return response.json()["response"]

def run_code_llm(prompt):
    return run_llm(prompt, model="deepseek-coder:6.7b-instruct")

def get_embedding(text):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text:latest", "prompt": text}
    )
    return response.json()["embedding"]

if __name__ == "__main__":
    print(run_llm("Explain quantum computing simply."))
    print(run_code_llm("Write a Python function to reverse a string."))
    print(get_embedding("Samplemind AI is awesome!"))
EOF
else
  echo "[=] Sample integration file already exists at $SAMPLE_FILE."
fi

echo "[✓] Samplemind AI Python dev environment is ready!"
echo "[i] Activate your environment with: source .venv/bin/activate"
echo "[i] Try: python $SAMPLE_FILE" 