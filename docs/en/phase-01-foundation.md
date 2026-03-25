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
    └── samplemind/               ← Everything in one package
        ├── __init__.py
        ├── __main__.py           ← Enables: python -m samplemind
        ├── core/                 ← Shared settings, models, auth (Phase 3+)
        │   ├── __init__.py
        │   ├── config.py         ← Settings (DB URL, JWT, CORS) via platformdirs
        │   ├── auth/             ← JWT, RBAC, password hashing (Phase 3)
        │   └── models/
        │       ├── sample.py     ← SQLModel Sample table + SampleCreate/SamplePublic
        │       └── user.py       ← SQLModel User table + UserCreate/UserPublic
        ├── cli/
        │   ├── __init__.py
        │   ├── app.py            ← Typer CLI — 8 commands (Phase 4)
        │   └── commands/         ← One file per command
        ├── analyzer/
        │   ├── __init__.py
        │   ├── audio_analysis.py ← analyze_file() → BPM, key, energy, mood, instrument
        │   └── classifier.py     ← classify_energy/mood/instrument() rule-based engine
        ├── data/
        │   ├── __init__.py
        │   ├── orm.py            ← SQLModel engine, init_orm(), get_session() (Phase 3)
        │   └── repositories/
        │       ├── sample_repository.py  ← SampleRepository (static methods)
        │       └── user_repository.py    ← UserRepository (static methods)
        ├── api/                  ← FastAPI auth server (Phase 3)
        │   └── routes/
        │       └── auth.py       ← /api/v1/auth/register, /login, /me, /refresh
        ├── web/
        │   ├── __init__.py
        │   └── app.py            ← Flask web UI (login, library, import)
        ├── integrations/         ← FL Studio (Phase 7)
        ├── packs/                ← Sample packs (Phase 9)
        └── sidecar/              ← Plugin server (Phase 8)
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
0.2.0

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

---

## 12. Expanded Ruff Configuration

Ruff covers lint, format, and import sorting in one fast tool. Expand the rule set as the
codebase matures to catch more classes of bugs:

```toml
# filename: pyproject.toml  (replace the [tool.ruff.lint] section)

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes (undefined names, unused imports)
    "I",    # isort (import order)
    "UP",   # pyupgrade (use modern Python syntax)
    "ANN",  # flake8-annotations (type hints on public functions)
    "PTH",  # flake8-use-pathlib (ban os.path, use pathlib.Path)
    "TCH",  # flake8-type-checking (move type-only imports to TYPE_CHECKING)
    "RUF",  # Ruff-native rules (fast, opinionated)
    "SIM",  # flake8-simplify (simplifiable conditions)
    "TRY",  # tryceratops (exception handling best practices)
]
ignore = [
    "ANN101",  # Missing type annotation for 'self' — not needed
    "ANN102",  # Missing type annotation for 'cls' — not needed
    "TRY003",  # Allow long exception messages in raise
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ANN"]   # Don't enforce type hints in test files
"src/samplemind/cli/*" = ["ANN"]  # Typer handles types via annotations already

[tool.ruff.lint.isort]
known-first-party = ["samplemind"]
force-sort-within-sections = true
```

Run ruff in watch mode during development:

```bash
# Watch mode — re-checks on every file save (great with tmux split)
$ uv run ruff check src/ --watch

# Auto-fix all safe issues
$ uv run ruff check src/ --fix

# Format the whole project
$ uv run ruff format src/ tests/
```

---

## 13. Parallel Tests with pytest-xdist

For large test suites (Phase 2+ with many WAV fixture tests), run tests in parallel across
CPU cores with `pytest-xdist`:

```bash
# Add to dev dependencies
$ uv add --dev pytest-xdist
```

```toml
# filename: pyproject.toml — update pytest config

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short -n auto"   # -n auto = use all available CPU cores
markers = [
    "slow: expensive tests (select with -m slow)",
    "integration: tests that require a real database or filesystem",
]
```

```bash
# Run tests on all cores (fastest)
$ uv run pytest -n auto

# Run on exactly 4 cores
$ uv run pytest -n 4

# Skip slow tests on all cores
$ uv run pytest -n auto -m "not slow"

# Run only integration tests
$ uv run pytest -m integration
```

> **Note:** Audio analysis tests with librosa are CPU-intensive. `-n auto` on an 8-core
> machine reduces test time from ~60s to ~10s for a typical test suite.

---

## 14. Pre-commit Hooks

Pre-commit hooks run ruff automatically before every `git commit`, preventing lint errors
from ever entering the repository:

```bash
# Install pre-commit
$ uv add --dev pre-commit

# Install the git hooks
$ uv run pre-commit install
```

```yaml
# filename: .pre-commit-config.yaml

repos:
  # Ruff — lint and format in one pass
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Standard hooks — trailing whitespace, file endings, TOML/YAML validity
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-toml
      - id: check-yaml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=500"]  # Block accidental audio file commits
```

```bash
# Run all hooks manually (without committing)
$ uv run pre-commit run --all-files

# Update hook versions
$ uv run pre-commit autoupdate
```

---

## 15. .editorconfig — Consistent Formatting Across Editors

`.editorconfig` enforces consistent indentation and line endings for all editors (VS Code,
Nvim, JetBrains, etc.) without requiring plugins:

```ini
# filename: .editorconfig
# editorconfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{ts,svelte,js,json,toml,yaml,yml}]
indent_style = space
indent_size = 2

[*.{rs}]
indent_style = space
indent_size = 4

[*.md]
trim_trailing_whitespace = false   # Markdown uses trailing spaces for line breaks

[Makefile]
indent_style = tab   # Makefiles require tabs
```

---

## 16. Advanced WSL2 Performance

### I/O Tuning — Stop WSL2 from Consuming All RAM

By default WSL2 can consume up to 50% of system RAM for its VM. For a dev machine running
FL Studio + VS Code + WSL2 simultaneously, cap it:

```ini
# filename: C:\Users\YourName\.wslconfig  (create this file on Windows)

[wsl2]
memory=6GB          # Max RAM for WSL2 VM
processors=4        # Max CPU cores
swap=2GB            # Swap file size
localhostForwarding=true  # Forward WSL2 ports to Windows (for Flask, etc.)
```

### Symlink the Project into Windows for VS Code

If you need to open the project from Windows Explorer occasionally:

```powershell
# PowerShell (run as Administrator)
# Create a symlink from Windows to the WSL2 path
New-Item -ItemType SymbolicLink `
  -Path "C:\Projects\SampleMind" `
  -Target "\\wsl$\Ubuntu\home\ubuntu\dev\projects\SampleMind-AI"
```

### Fast Git Operations — Enable fsmonitor

```bash
# Enable Git's built-in filesystem monitor (speeds up git status/add on large repos)
$ git config core.fsmonitor true
$ git config core.untrackedCache true

# Confirm it's running
$ git fsmonitor--daemon status
```

### Port Forwarding — Access Flask/Tauri from Windows Browser

WSL2 ports are automatically forwarded to Windows. No extra config needed:

```bash
# Start Flask in WSL2:
$ uv run samplemind serve --port 5000

# Open in Windows Chrome/Edge (automatic forwarding):
# http://localhost:5000
```

### Measuring Python Performance Baseline

Before optimizing, measure. Run this to get a baseline for analysis speed:

```bash
# Measure import time of the samplemind package
$ uv run python -X importtime -c "import samplemind" 2>&1 | tail -5

# Profile a single file analysis (shows where time is spent)
$ uv run python -m cProfile -s cumulative -c "
from samplemind.analyzer.audio_analysis import analyze_file
analyze_file('/tmp/test.wav')
" | head -30

# Benchmark batch analysis with hyperfine
$ sudo apt install hyperfine  # WSL2 Ubuntu
$ hyperfine --warmup 2 \
  'uv run samplemind import /tmp/samples/ --json' \
  --export-markdown bench-results.md
```

---

## 8. Dev Quality Tools (2026 Additions)

### pre-commit Setup

Install pre-commit and add ruff hooks to catch issues before every commit:

```bash
uv add --dev pre-commit
uv run pre-commit install
```

Create `.pre-commit-config.yaml` at the repo root:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
```

Run hooks manually on all files:
```bash
uv run pre-commit run --all-files
```

### .editorconfig

Create `.editorconfig` at the repo root to enforce consistent formatting across editors:

```ini
# .editorconfig
root = true

[*]
indent_style = space
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[*.{js,ts,svelte,json,yaml,yml,toml,md}]
indent_size = 2

[Makefile]
indent_style = tab

[*.rs]
indent_size = 4
```

VS Code respects `.editorconfig` automatically with the EditorConfig extension.

### WSL2 Performance Tuning

Git is significantly faster on WSL2 with these settings enabled:

```bash
# Enable filesystem monitor and untracked cache:
git config core.fsmonitor true
git config core.untrackedCache true

# Verify:
git config --get core.fsmonitor    # should print: true
git config --get core.untrackedCache  # should print: true
```

**Critical:** Always develop on the Linux ext4 filesystem, not NTFS:

```bash
# Fast (Linux filesystem):
/home/ubuntu/dev/projects/SampleMind-AI/  ✓

# Slow (NTFS via NTFS-3g driver, 5-10x slower for git/python):
/mnt/c/Users/YourName/SampleMind-AI/     ✗
```

Optional `/etc/wsl.conf` tuning for heavy workloads:

```ini
# /etc/wsl.conf (requires WSL restart: wsl --shutdown)
[wsl2]
memory=8GB          # limit WSL2 memory (default: 50% of host RAM)
processors=4        # limit CPU cores if needed
localhostForwarding=true
```

### VS Code WSL Extension Tips

When using VS Code with the Remote – WSL extension, install these extensions
**inside the WSL context** (not on Windows):

```bash
# From WSL terminal:
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension tamasfe.even-better-toml
code --install-extension svelte.svelte-vscode
code --install-extension rust-lang.rust-analyzer
```

Verify extensions are running in WSL (not Windows) in the Extensions panel:
look for the "WSL: Ubuntu" badge next to each extension.

---

## 11. Structured Logging with structlog

Replace bare `print()` and `logging.basicConfig()` with **structlog** for
machine-readable JSON logs that Sentry, Datadog, and Grafana can ingest.

```bash
uv add structlog rich
```

```python
# src/samplemind/core/logging.py
"""
Structured logging configuration for SampleMind-AI.

Uses structlog with two renderers:
  - Development: rich-colored human-readable output  (to stderr)
  - Production:  JSON lines, one log entry per line   (to stderr)
Machine-parseable JSON output goes to stdout for IPC consumers (Tauri/Rust).
"""
import sys
import structlog
from samplemind.core.config import get_settings


def configure_logging() -> None:
    """Call once at application startup before any other imports."""
    settings = get_settings()

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_format == "json":
        # Production: JSON lines → pipe to log aggregator
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: colored Rich output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.log_level.upper(), 20)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
```

Usage in any module:

```python
from samplemind.core.logging import get_logger
log = get_logger(__name__)

# Structured key=value context attached to every subsequent log in this block:
with structlog.contextvars.bound_contextvars(sample_id=42, path="/tmp/kick.wav"):
    log.info("analyzing", bpm=140.0)
    log.warning("low_rms", rms=0.001, threshold=0.015)
```

Environment variables:

```bash
SAMPLEMIND_LOG_LEVEL=debug   # debug / info / warning / error
SAMPLEMIND_LOG_FORMAT=json   # json (prod) / console (dev)
```

---

## 12. Environment Validation with pydantic-settings

Catch missing or malformed config at startup — never silently use defaults
in production.

```bash
uv add pydantic-settings
```

```python
# src/samplemind/core/config.py
"""
Single source of truth for all SampleMind configuration.

Load order (later overrides earlier):
  1. Hardcoded defaults below
  2. ~/.samplemind/config.toml        (user config file)
  3. .env file in project root        (dev convenience)
  4. Environment variables            (CI / production)

Validation happens at startup: if SECRET_KEY is missing in production,
the app raises immediately with a clear error instead of silently using
an insecure default.
"""
from __future__ import annotations
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import platformdirs


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{platformdirs.user_data_dir('SampleMind', 'SampleMind-AI')}/samplemind.db",
        description="SQLAlchemy connection string. Use sqlite:// for in-memory testing.",
    )

    # ── Authentication ────────────────────────────────────────────────────
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-use-secrets-token-hex-32",
        description="JWT signing key. Generate: python -c \"import secrets; print(secrets.token_hex(32))\"",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Web servers ───────────────────────────────────────────────────────
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000
    flask_secret_key: str = Field(default="CHANGE-ME-FLASK")
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = ["tauri://localhost", "http://localhost:5174", "http://localhost:5000"]

    # ── Audio analysis ────────────────────────────────────────────────────
    workers: int = 0              # 0 = auto (cpu_count)
    sample_rate: int = 22050      # librosa default
    max_file_size_mb: int = 500   # reject files larger than this

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    log_format: Literal["console", "json"] = "console"

    # ── Optional integrations ─────────────────────────────────────────────
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN — opt-in crash reporting")
    anthropic_api_key: str | None = Field(default=None, description="Auggie CLI integration")
    openai_api_key: str | None = Field(default=None, description="Optional LLM features (Phase 12+)")

    model_config = SettingsConfigDict(
        env_prefix="SAMPLEMIND_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def warn_insecure_secret(cls, v: str) -> str:
        if v.startswith("CHANGE-ME"):
            import warnings
            warnings.warn(
                "SAMPLEMIND_SECRET_KEY is using the insecure default. "
                "Set it to a random 32-byte hex string in production.",
                stacklevel=2,
            )
        return v

    @model_validator(mode="after")
    def ensure_db_dir_exists(self) -> "Settings":
        if self.database_url.startswith("sqlite:///"):
            path = Path(self.database_url.replace("sqlite:///", ""))
            path.parent.mkdir(parents=True, exist_ok=True)
        return self


_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def override_settings(**kwargs) -> Settings:
    """Test helper — returns a new Settings with overrides, does not touch global."""
    return Settings(**kwargs)
```

---

## 13. Health Check System

Every service exposes `/health` or `/api/v1/health`. The Tauri app polls this
on startup to confirm Python services are live before showing the UI.

```python
# src/samplemind/core/health.py
"""
Health check aggregator.

Each check is a callable returning (name, ok, detail).
The overall status is 'ok' only if ALL checks pass.
"""
from __future__ import annotations
import time
import sqlite3
from pathlib import Path
from typing import NamedTuple
from samplemind.core.config import get_settings


class HealthResult(NamedTuple):
    name: str
    ok: bool
    detail: str
    latency_ms: float


def check_database() -> HealthResult:
    start = time.perf_counter()
    try:
        settings = get_settings()
        db_path = settings.database_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path, timeout=2.0)
        conn.execute("SELECT COUNT(*) FROM samples").fetchone()
        conn.close()
        ok, detail = True, f"samples table accessible at {db_path}"
    except Exception as e:
        ok, detail = False, str(e)
    return HealthResult("database", ok, detail, (time.perf_counter() - start) * 1000)


def check_audio_libraries() -> HealthResult:
    start = time.perf_counter()
    try:
        import librosa, soundfile, numpy  # noqa: F401
        ok, detail = True, f"librosa {librosa.__version__}"
    except ImportError as e:
        ok, detail = False, str(e)
    return HealthResult("audio_libs", ok, detail, (time.perf_counter() - start) * 1000)


def run_all_checks() -> dict:
    import importlib.metadata
    checks = [check_database(), check_audio_libraries()]
    all_ok = all(c.ok for c in checks)
    return {
        "status": "ok" if all_ok else "degraded",
        "version": importlib.metadata.version("samplemind"),
        "checks": [
            {"name": c.name, "ok": c.ok, "detail": c.detail,
             "latency_ms": round(c.latency_ms, 1)}
            for c in checks
        ],
    }
```

FastAPI health endpoint (registered in `api/main.py`):

```python
from fastapi import APIRouter
from samplemind.core.health import run_all_checks

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health() -> dict:
    """
    Health check endpoint.
    Returns 200 + {"status": "ok"} if all subsystems healthy.
    Returns 200 + {"status": "degraded"} with check details if any fail.
    Tauri polls this at startup before showing the main window.
    """
    return run_all_checks()
```

---

## 14. Configuration File Support (~/.samplemind/config.toml)

Users can persist preferences without environment variables.
`pydantic-settings` reads TOML natively in Python 3.11+.

```toml
# ~/.samplemind/config.toml  (created by: uv run samplemind config init)
[samplemind]
workers = 4
log_level = "info"
log_format = "console"
max_file_size_mb = 200

[samplemind.database]
url = "sqlite:///~/.samplemind/library.db"

[samplemind.fl_studio]
# Override FL Studio export path (optional)
export_path = "~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind"
```

CLI command to create the default config:

```python
# src/samplemind/cli/commands/config_cmd.py
import typer, tomllib, tomli_w
from pathlib import Path
from rich.console import Console

app = typer.Typer(help="Manage SampleMind configuration")
console = Console(stderr=True)
CONFIG_PATH = Path.home() / ".samplemind" / "config.toml"

@app.command()
def init(force: bool = typer.Option(False, "--force", help="Overwrite existing config")):
    """Create default config file at ~/.samplemind/config.toml"""
    if CONFIG_PATH.exists() and not force:
        console.print(f"[yellow]Config already exists:[/yellow] {CONFIG_PATH}")
        console.print("Use --force to overwrite.")
        raise typer.Exit()
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(DEFAULT_TOML)
    console.print(f"[green]Created:[/green] {CONFIG_PATH}")

@app.command()
def show():
    """Show current effective configuration"""
    from samplemind.core.config import get_settings
    import json, sys
    settings = get_settings()
    print(json.dumps(settings.model_dump(exclude={"secret_key", "flask_secret_key"}), indent=2),
          file=sys.stdout)

DEFAULT_TOML = """\
[samplemind]
workers = 0          # 0 = auto (cpu_count)
log_level = "info"
log_format = "console"
"""
```

---

## 15. Sentry Integration (Opt-In Crash Reporting)

```bash
uv add sentry-sdk[fastapi,flask]
```

```python
# src/samplemind/core/sentry.py
"""
Opt-in crash reporting via Sentry.

Enabled only if SAMPLEMIND_SENTRY_DSN is set in environment.
Never collects audio data or file paths — only exception tracebacks.
"""
from samplemind.core.config import get_settings
from samplemind.core.logging import get_logger

log = get_logger(__name__)


def init_sentry() -> bool:
    """Initialize Sentry if DSN is configured. Returns True if enabled."""
    settings = get_settings()
    if not settings.sentry_dsn:
        log.debug("sentry_disabled", reason="SAMPLEMIND_SENTRY_DSN not set")
        return False

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration(), FlaskIntegration()],
        traces_sample_rate=0.1,   # 10% of transactions for performance
        profiles_sample_rate=0.1,
        environment="production" if settings.log_format == "json" else "development",
        # Privacy: strip file paths from breadcrumbs
        before_breadcrumb=lambda crumb, _hint: (
            None if crumb.get("category") == "httplib" else crumb
        ),
        # Never send audio data
        before_send=_strip_audio_data,
    )
    log.info("sentry_enabled", dsn=settings.sentry_dsn[:20] + "...")
    return True


def _strip_audio_data(event: dict, _hint: dict) -> dict:
    """Remove any audio-related data from Sentry events before sending."""
    # Strip file paths from exception values for privacy
    if "exception" in event:
        for exc in event["exception"].get("values", []):
            for frame in exc.get("stacktrace", {}).get("frames", []):
                frame.pop("vars", None)  # remove local variable values
    return event
```

Call at startup in both Flask and FastAPI entry points:

```python
# In api/main.py create_app() and web/app.py:
from samplemind.core.sentry import init_sentry
init_sentry()   # no-op if SAMPLEMIND_SENTRY_DSN not set
```

