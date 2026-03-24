# Phase 1 — Foundation & Project Structure

> Set up a modern Python 3.13 project with `uv`, `pyproject.toml`, and a clean folder layout
> that scales through all 10 phases.

---

## Prerequisites

- Git installed and configured
- WSL2 (Windows Subsystem for Linux 2) on Windows, or native terminal on macOS
- VS Code with WSL extension (Remote – WSL) on Windows
- No existing Python environment needed — `uv` handles everything

---

## Goal State

```
SampleMind-AI/
├── pyproject.toml          ← Replaces requirements.txt
├── .python-version         ← Pins Python 3.13
├── uv.lock                 ← Deterministic dependency lock
├── src/
│   └── samplemind/         ← Proper package layout (src-layout)
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       ├── analyzer/
│       ├── data/
│       └── web/
├── tests/
│   └── conftest.py
├── scripts/
│   └── setup-dev.sh
└── app/                    ← Tauri desktop app (unchanged this phase)
```

After `uv sync` you can run `samplemind --help` directly without manually activating a virtual
environment.

---

## 1. Why Switch from pip/venv to uv?

`uv` (from Astral) is a Rust-based package manager that replaces `pip`, `pip-tools`, and `venv`
with a single binary. It is 10–100× faster than pip.

```
pip + venv (old)              uv (new)
─────────────────────         ──────────────────────────────
python -m venv .venv          (automatic)
source .venv/bin/activate     (not needed)
pip install -r requirements   uv sync
pip install package           uv add package
pip freeze > requirements     (uv.lock auto-managed)
```

Key advantages:
- `uv.lock` is deterministic — all contributors get identical versions
- Removes only packages you explicitly asked for on `uv remove` (no orphans)
- Single static binary — no Python installation needed to bootstrap the environment

---

## 2. Install uv

### WSL2 / Linux / macOS

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (append to ~/.bashrc or ~/.zshrc):
$ export PATH="$HOME/.cargo/bin:$PATH"

# Confirm installation:
$ uv --version
uv 0.5.x
```

### Windows (PowerShell, without WSL2)

```powershell
$ powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Recommendation:** Use WSL2 for development on Windows. Commands are then identical to macOS.

---

## 3. pyproject.toml — Project Configuration Hub

`pyproject.toml` replaces `requirements.txt` and consolidates all configuration (dependencies,
linting, testing) in one place. This is the PEP 517/518/621 standard for modern Python projects.

```toml
# filename: pyproject.toml

[project]
name = "samplemind"
version = "0.1.0"
description = "AI-driven sample library and DAW companion for FL Studio"
authors = [{ name = "lchtangen" }]
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.13"

# ─── Runtime dependencies (replaces requirements.txt) ────────────────────────
dependencies = [
    # Audio analysis
    "librosa==0.11.0",
    "numpy>=2.2",
    "scipy>=1.15",
    "soundfile>=0.13",
    "soxr>=0.5",

    # Machine learning
    "scikit-learn>=1.6",
    "numba>=0.61",

    # Web server
    "flask>=3.1",
    "jinja2>=3.1",

    # Database ORM (upgraded from raw sqlite3 in Phase 3)
    "sqlmodel>=0.0.21",

    # CLI (upgraded from argparse in Phase 4)
    "typer>=0.12",
    "rich>=13",

    # Utilities
    "requests>=2.32",
    "platformdirs>=4.3",
]

# ─── Optional dependencies (install with: uv sync --extra dev) ───────────────
[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov",
    "ruff>=0.4",
]

# ─── CLI entry point ─────────────────────────────────────────────────────────
# After `uv sync`, `samplemind` is available directly in the terminal
[project.scripts]
samplemind = "samplemind.cli.app:app"

# ─── Build configuration ─────────────────────────────────────────────────────
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Tell hatchling that source code lives in src/
[tool.hatch.build.targets.wheel]
packages = ["src/samplemind"]

# ─── pytest configuration ─────────────────────────────────────────────────────
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
# Markers: run only fast tests with: pytest -m "not slow"
markers = ["slow: expensive tests (select with -m slow)"]

# ─── Ruff linting configuration ───────────────────────────────────────────────
[tool.ruff]
src = ["src"]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]   # pycodestyle + pyflakes + isort + pyupgrade
```

---

## 4. New Folder Structure (src-layout)

### Why src-layout?

With flat layout (`src/analyzer/`) Python can import directly from the source folder, hiding
installation errors. With `src/samplemind/` you get `ModuleNotFoundError` if the package isn't
properly installed — catching problems early.

```
# OLD (flat layout — can hide import errors)
SampleMind-AI/
└── src/
    ├── analyzer/
    │   └── audio_analysis.py
    ├── cli/
    └── main.py

# NEW (src-layout — standard for distributable packages)
SampleMind-AI/
└── src/
    └── samplemind/           ← Everything in one package
        ├── __init__.py
        ├── __main__.py       ← Enables: python -m samplemind
        ├── cli/
        │   ├── __init__.py
        │   ├── app.py        ← Typer CLI (Phase 4)
        │   └── commands/
        ├── analyzer/
        │   ├── __init__.py
        │   ├── audio_analysis.py
        │   └── classifier.py
        ├── data/
        │   ├── __init__.py
        │   └── database.py   → models.py + repository.py (Phase 3)
        ├── web/
        │   ├── __init__.py
        │   └── app.py
        ├── integrations/     ← FL Studio (Phase 7)
        ├── packs/            ← Sample packs (Phase 9)
        └── sidecar/          ← Plugin server (Phase 8)
```

---

## 5. Package __init__.py and __main__.py

```python
# filename: src/samplemind/__init__.py

# Version number — used by CLI and Tauri to display version
__version__ = "0.1.0"
```

```python
# filename: src/samplemind/__main__.py

# Enables: python -m samplemind [command]
# Useful in Tauri integration where we call Python as a subprocess
from samplemind.cli.app import app

if __name__ == "__main__":
    app()
```

---

## 6. .python-version — Pin Python Version

```
# filename: .python-version
3.13
```

`uv` reads this file automatically and uses Python 3.13 for all operations in the project.

---

## 7. Daily uv Commands

```bash
# First-time setup (installs all dependencies)
$ uv sync --extra dev

# Add a new package (updates pyproject.toml and uv.lock)
$ uv add packagename

# Add a dev dependency
$ uv add --dev packagename

# Remove a package
$ uv remove packagename

# Run a command in the project environment (no manual activation needed)
$ uv run python -m samplemind analyze ~/Music/samples/

# Run tests
$ uv run pytest

# Run linting
$ uv run ruff check src/
```

---

## 8. VS Code Setup for WSL2

Add / update `.vscode/settings.json`:

```json
// filename: .vscode/settings.json
{
    // ── Python ──────────────────────────────────────────────────────────
    // Point VS Code to uv's virtual environment
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.analysis.extraPaths": ["${workspaceFolder}/src"],

    // ── Ruff linting (replaces pylint/flake8) ───────────────────────────
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },

    // ── Rust (for Tauri development) ─────────────────────────────────────
    "rust-analyzer.linkedProjects": ["app/src-tauri/Cargo.toml"],

    // ── WSL2-specific: use LF line endings ──────────────────────────────
    "files.eol": "\n",

    // ── File exclusions (hide from file explorer) ────────────────────────
    "files.exclude": {
        "**/__pycache__": true,
        "**/.venv": true,
        "**/node_modules": true,
        "**/target": true
    }
}
```

---

## 9. Bootstrap Script for New Contributors

```bash
#!/usr/bin/env bash
# filename: scripts/setup-dev.sh
# Run: bash scripts/setup-dev.sh
# Sets up the entire development environment from scratch.

set -e  # Exit on error

echo "=== SampleMind AI — Development Environment Setup ==="

# ── 1. Check uv is installed ──────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "uv version: $(uv --version)"

# ── 2. Install Python + dependencies ─────────────────────────────────────────
echo "Installing Python 3.13 and dependencies..."
uv sync --extra dev

# ── 3. Confirm installation ───────────────────────────────────────────────────
echo "Confirming installation..."
uv run python -c "import samplemind; print(f'samplemind {samplemind.__version__} OK')"
uv run python -c "import librosa; print(f'librosa {librosa.__version__} OK')"

# ── 4. Run tests ──────────────────────────────────────────────────────────────
echo "Running tests..."
uv run pytest tests/ -x --tb=short

echo ""
echo "=== Setup complete! ==="
echo "Run: uv run samplemind --help"
```

---

## 10. WSL2-Specific Considerations

### Filesystem Performance

WSL2 has two filesystems:
- `/home/user/` (Linux ext4) — **fast**, use this for source code
- `/mnt/c/` (Windows NTFS, mounted) — **slow** for Python/Git

```bash
# RECOMMENDED: Work in the Linux filesystem
$ cd ~/dev/projects/SampleMind-AI

# AVOID: Don't work from the Windows folder (slow!)
# cd /mnt/c/Users/YourName/Projects/SampleMind-AI
```

### Line Endings

Configure Git to use LF (`\n`) — macOS-compatible:

```bash
# Set globally for WSL2:
$ git config --global core.autocrlf false
$ git config --global core.eol lf
```

### Developing for macOS from WSL2

You develop on WSL2 (Linux), but the product runs on macOS. This means:
- The code (Python, Rust) is cross-platform — works on both
- Building Tauri for macOS **requires** a macOS machine or GitHub Actions with `macos-latest`
- File paths: always use `pathlib.Path` in Python, never hardcoded slashes

```python
# Correct — works on all platforms
from pathlib import Path
db_path = Path.home() / ".samplemind" / "library.db"

# Wrong — crashes on Windows
db_path = os.path.expanduser("~") + "/.samplemind/library.db"
```

---

## 11. Migrating from Existing Setup

Step-by-step from the old `requirements.txt` setup:

```bash
# Step 1: Create pyproject.toml (use content from section 3 above)

# Step 2: Delete the old virtual environment
$ rm -rf .venv/

# Step 3: Create .python-version
$ echo "3.13" > .python-version

# Step 4: Install with uv
$ uv sync --extra dev

# Step 5: Confirm old CLI commands still work
$ uv run python src/main.py --help

# Step 6: Move source code to src/samplemind/ (done gradually in Phases 2-4)
# src/analyzer/     → src/samplemind/analyzer/
# src/cli/          → src/samplemind/cli/
# src/data/         → src/samplemind/data/
# src/web/          → src/samplemind/web/
# src/main.py       → src/samplemind/cli/app.py (Phase 4)
```

---

## Migration Notes

- `requirements.txt` is kept temporarily during migration, deleted when `pyproject.toml` is complete
- All import paths (`from analyzer.audio_analysis import`) update to `from samplemind.analyzer.audio_analysis import` in Phases 2–4
- `src/main.py` is replaced by `src/samplemind/cli/app.py` (Typer) in Phase 4

---

## Testing Checklist

```bash
# Confirm uv is installed and works
$ uv --version

# Confirm Python 3.13
$ uv run python --version
Python 3.13.x

# Confirm samplemind package imports correctly
$ uv run python -c "import samplemind; print(samplemind.__version__)"
0.1.0

# Confirm all dependencies are installed
$ uv run python -c "import librosa, flask, sqlmodel, typer; print('All OK')"

# Run tests (none yet, but confirm pytest works)
$ uv run pytest tests/ -v
```

---

## Troubleshooting

**Error: `uv: command not found` after installation**
```bash
# Add uv to PATH manually:
$ export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.bashrc for permanent effect
```

**Error: `ModuleNotFoundError: No module named 'samplemind'`**
```bash
# Install package in editable mode:
$ uv pip install -e .
# Or re-sync:
$ uv sync
```

**Error: Python 3.13 not available**
```bash
# uv can install Python for you:
$ uv python install 3.13
$ uv sync
```

**Error: Slow performance in WSL2**
```bash
# Confirm you are working in the Linux filesystem, not /mnt/c/:
$ pwd
/home/yourusername/dev/projects/SampleMind-AI  # ← Correct
# /mnt/c/Users/...  ← Wrong, move the project
```
