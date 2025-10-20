#!/bin/bash
# SampleMind AI v6 - Quick Start Script

set -e

echo "🚀 SampleMind AI v6 - Quick Start Setup"
echo "======================================"

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m pip install --upgrade pip
pip install poetry
poetry install

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
poetry run pre-commit install

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d mongodb redis chromadb

# Install AI models
echo "🤖 Installing AI models..."
if command -v ollama >/dev/null 2>&1; then
    ollama pull phi3:mini
    ollama pull qwen2.5:7b-instruct
else
    echo "⚠️ Ollama not found. Install from https://ollama.ai"
fi

echo "✅ Setup complete! Run 'make dev' to start the server."
