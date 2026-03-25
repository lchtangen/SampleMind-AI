#!/usr/bin/env bash
# setup-dev.sh — SampleMind AI development environment setup
# Works on: WSL2 Ubuntu 24.04, macOS 12+
# Usage: bash scripts/setup-dev.sh

set -euo pipefail

# --- Color helpers ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo "========================================"
echo "  SampleMind AI — Dev Environment Setup"
echo "========================================"
echo ""

# --- Detect OS and warn about WSL2 path ---
OS="$(uname -s)"
if [[ "$OS" == "Linux" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    PLATFORM="wsl2"
    info "Detected WSL2 Ubuntu"
    CWD="$(pwd)"
    if [[ "$CWD" == /mnt/c/* ]]; then
        error "Working directory is on NTFS (/mnt/c/...). Move project to Linux filesystem first:
  cp -r /mnt/c/path/to/SampleMind-AI ~/dev/projects/
  cd ~/dev/projects/SampleMind-AI
  bash scripts/setup-dev.sh"
    fi
    ok "Project is on Linux ext4 filesystem"
elif [[ "$OS" == "Darwin" ]]; then
    PLATFORM="macos"
    info "Detected macOS"
else
    PLATFORM="linux"
    info "Detected Linux"
fi

# --- Check: uv (Python package manager) ---
echo ""
info "Checking Python toolchain (uv)..."
if ! command -v uv &>/dev/null; then
    warn "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    ok "uv installed: $(uv --version)"
else
    ok "uv found: $(uv --version)"
fi

# --- Python deps ---
echo ""
info "Syncing Python 3.13 environment and dependencies..."
uv sync --extra dev
ok "Python deps synced"

# --- Verify core imports ---
echo ""
info "Verifying core Python imports..."
uv run python -c "import samplemind; print(f'  samplemind {samplemind.__version__} OK')"
uv run python -c "import librosa; print(f'  librosa {librosa.__version__} OK')"
uv run python -c "import soundfile; print(f'  soundfile OK')"
uv run python -c "import typer; print(f'  typer OK')"
ok "All core imports verified"

# --- Ruff lint check ---
echo ""
info "Running ruff lint check..."
if uv run ruff check src/ --quiet; then
    ok "ruff: no lint issues"
else
    warn "ruff found issues — run: uv run ruff check src/ for details"
fi

# --- Run tests ---
echo ""
info "Running test suite..."
set +e
uv run pytest tests/ -x --tb=short -q
CODE=$?
set -e
if [[ $CODE -eq 5 ]]; then
    warn "No tests found yet (exit code 5) — continuing"
elif [[ $CODE -ne 0 ]]; then
    error "Tests failed — check output above"
else
    ok "All tests passed"
fi

# --- git fsmonitor (WSL2 performance) ---
echo ""
info "Configuring git performance settings..."
git config core.fsmonitor true
git config core.untrackedcache true
ok "git fsmonitor + untrackedcache enabled"

# --- pre-commit hooks ---
echo ""
info "Installing pre-commit hooks..."
if uv run pre-commit --version &>/dev/null; then
    uv run pre-commit install
    ok "pre-commit hooks installed (ruff check + ruff format on staged files)"
else
    warn "pre-commit not available — skipping hook install"
fi

# --- Node / pnpm (optional, for Tauri desktop app) ---
echo ""
info "Checking Node.js / pnpm (required for Tauri desktop app)..."
if command -v node &>/dev/null; then
    ok "node: $(node --version)"
else
    warn "node not found — install via nvm or: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -"
fi
if command -v pnpm &>/dev/null; then
    ok "pnpm: $(pnpm --version)"
else
    warn "pnpm not found — install: npm install -g pnpm"
fi

# --- Rust / Cargo (optional, for Tauri desktop app) ---
echo ""
info "Checking Rust toolchain (required for Tauri desktop app)..."
if command -v cargo &>/dev/null; then
    ok "cargo: $(cargo --version)"
else
    warn "Rust not found — install: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
fi

# --- Summary ---
echo ""
echo "========================================"
echo "  Setup Complete"
echo "========================================"
echo ""
echo "  Quick start:"
echo "    uv run samplemind --help"
echo "    uv run samplemind serve            # Flask web UI at http://localhost:5000"
echo "    uv run pytest tests/ -v            # run tests"
echo "    uv run ruff check src/             # lint"
echo ""
echo "  Desktop app (requires node + pnpm + cargo):"
echo "    cd app && pnpm install && pnpm tauri dev"
echo ""
echo "  Docs: docs/en/phase-01-foundation.md through phase-10-production.md"
echo ""
