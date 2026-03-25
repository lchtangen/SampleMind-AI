---

## FL Studio Context

SampleMind integrates with FL Studio via:
1. Filesystem export
2. Clipboard paths
3. AppleScript automation on macOS
4. MIDI metadata signaling
5. JUCE VST3/AU plugin flows

Assume macOS-first behavior for FL Studio automation unless user explicitly targets Windows.

---
---

## What Not to Suggest

- pip install for project dependency management
- python -m venv as primary workflow
- black, flake8, pylint, isort as the default lint stack
- npm in app/ when pnpm is the project standard
- sys.path.insert hacks in new code
- committing real audio fixtures
- breaking legacy src/main.py runtime contract without coordinated Tauri update

---
---

## Tooling and Environment

**Python:**

- .venv at repo root is expected.
- VS Code settings already target ${workspaceFolder}/.venv/bin/python.

**Workspace commands:**

- Prefer existing project scripts and tasks where available.

**File path handling:**

- Prefer platformdirs for new cross-platform config/data locations.
- Avoid introducing new hardcoded home-directory paths in new code.

---
---

## Testing and Quality

**Testing rules:**

1. Never commit real audio files.
2. Use synthetic WAV fixtures in tests/conftest.py.
3. Use in-memory SQLite for DB tests.

Preferred test commands:

```bash
uv run pytest tests/ -v
uv run pytest -m "not slow"
```

**Lint/format rules:**

- Use ruff only for Python lint and format guidance.
- Do not suggest black/flake8/pylint/isort for new workflows.

---
---

## Web and Desktop Rules

**Flask:**

- Keep API responses stable for app/src/static/app.js and desktop consumers.
- Prefer additive API changes over breaking response shape changes.

**Tauri/Rust:**

- Async commands must use owned input types (String, not &str).
- Return Result<T, String> and map errors with to_string().
- Register new commands in invoke_handler.

**Frontend:**

- If adding Svelte in app/src, use Svelte 5 Runes patterns.

**Package manager for app/:**

- Prefer pnpm commands for guidance and scripts.

---
---

## Database Rules

**Current runtime:** sqlite3 implementation is active.
**Target:** SQLModel + Alembic migration path is planned and partially scaffolded in docs.

Guideline:

- For incremental features in current runtime paths, keep sqlite3 compatibility.
- For explicit Phase 3 migration tasks, prefer SQLModel + Alembic and migrate end-to-end.

---
stores metadata in SQLite, and surfaces everything through a CLI, Flask web UI, Tauri desktop app,
and JUCE VST3/AU plugin — all reading the same database.

# SampleMind-AI — Claude Code Project Guide (2026)

> AI-powered audio sample library manager for FL Studio (macOS primary, Windows secondary).
> Development: Windows WSL2. Production: macOS 12+ Universal Binary.

## Core Engineering Rules

1. **Read the actual source file before proposing changes.**
2. **Respect migration state; keep compatibility unless user asks for a hard cutover.**
3. **Prefer minimal, safe edits over broad refactors.**
4. **Preserve Tauri/Python IPC contracts.**
5. **Prefer updating existing files over introducing new architecture layers.**

---

## Project Overview

SampleMind-AI analyzes WAV/AIFF sample files with librosa (BPM, key, instrument, mood, energy), stores metadata in SQLite, and surfaces everything through a CLI, Flask web UI, Tauri desktop app, and JUCE VST3/AU plugin — all reading the same database.

**Key docs:**

- [ARCHITECTURE.md](ARCHITECTURE.md) — system diagram, IPC contract table
- [docs/en/phase-01-foundation.md](docs/en/phase-01-foundation.md) through [docs/en/phase-10-production.md](docs/en/phase-10-production.md) — phase upgrade path

---

## Repository Layout

| Path | Contents |
|------|----------|
| `src/` | Python backend (legacy + new src/samplemind/) |
| `src/analyzer/` | librosa feature extraction, classifiers |
| `src/cli/` | CLI commands (legacy argparse) |
| `src/data/` | Database layer (sqlite3, legacy) |
| `src/web/` | Flask web UI |
| `src/samplemind/` | New src-layout package (Phase 1+) |
| `app/` | Tauri 2 desktop app |
| `app/src/` | Svelte 5 frontend |
| `app/src-tauri/` | Rust backend, IPC |
| `plugin/` | JUCE 8 VST3/AU plugin |
| `docs/en/` | English phase docs |
| `docs/no/` | Norwegian phase docs |
| `scripts/` | Shell scripts |
| `.claude/commands/` | Project slash commands (skills) |
| `.claude/agents/` | Project subagent definitions |
| `.github/workflows/` | CI/CD: python-lint.yml (legacy), ci.yml (target) |

---

## Migration State (2026)

| Component | Current | Target |
|---|---|---|
| Package manager | uv + pyproject.toml | (live) |
| Python version | 3.13 | (live) |
| Package layout | src/samplemind/ | (live) |
| CLI | Typer (src/samplemind/cli/app.py) | (live) |
| Database | sqlite3 (src/samplemind/data/database.py) | SQLModel + Alembic (planned) |
| Lint/format | ruff | (live) |
| Frontend | Svelte 5 Runes + Vite | (live) |
| Tests | pytest + soundfile fixtures | (live) |
| CI | python-lint.yml (pip+black, legacy) | ci.yml + release.yml (planned) |
| Plugin | JUCE 8 VST3/AU | (planned) |

**Important:**

- **Legacy and new code paths coexist.**
- **src/main.py** (legacy argparse CLI) is still required for Tauri dev mode. Do not break this entrypoint unless you also update app/src-tauri/src/main.rs.
- **Migration must be incremental and non-breaking.**

---

## Development Environment

### Windows WSL2 (development)

```bash
# Code lives HERE (Linux ext4 filesystem — fast):
/home/ubuntu/dev/projects/SampleMind-AI/

# NEVER put code here (NTFS — 5-10× slower):
/mnt/c/...

# Open VS Code from WSL terminal:
code .
```

### macOS (production target — test before release)

```bash
# Prerequisites:
xcode-select --install
brew install uv pnpm rustup

# Production build:
cd app && pnpm tauri build --target universal-apple-darwin
```

### Common Commands

```bash
# --- Python (current, uses venv) ---
source .venv/bin/activate
python src/main.py list
python src/web/app.py              # Flask at http://localhost:5000

# --- Python (target, uses uv — Phase 1+) ---
uv sync                            # install deps
uv run samplemind list
uv run samplemind serve
uv run pytest tests/ -v
uv run ruff check src/
uv run ruff format src/

# --- Tauri desktop app ---
cd app && pnpm install
pnpm tauri dev                     # dev mode (HMR)
pnpm tauri build                   # production

# --- Rust ---
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cargo test --manifest-path app/src-tauri/Cargo.toml

# --- JUCE plugin (Phase 8, macOS) ---
cd plugin && cmake -B build && cmake --build build
auval -v aufx SmPl SmAI

# --- Python sidecar (for JUCE testing) ---
uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock &
```

---

## Python Standards

**Package manager:**

- Use `uv` only for Python dependency and execution workflows.
- Do not suggest `pip install` for project work.

**Preferred commands:**

```bash
uv sync
uv run samplemind --help
uv run pytest
uv run ruff check src/
uv run ruff format src/
```

**Type hints:**

- Required on all new public functions/methods.

**Imports:**

- Prefer src-layout imports for new code:

```python
from samplemind.analyzer.audio_analysis import analyze_file
```

- Avoid `sys.path.insert` hacks in new code.
- Exception: If touching legacy files that already rely on legacy import patterns, do not rewrite unrelated import architecture unless requested.

**CLI and IPC Contract:**

- Use Typer for new CLI features in src/samplemind/cli.
- **Critical stdout/stderr split:**
  - JSON intended for machine consumption must go to stdout only.
  - Human-readable output must go to stderr (or non-JSON mode where appropriate).
- **Reason:** Rust/Tauri and future sidecar flows parse stdout; mixed output breaks integration silently.
- **Migration safety:** Do not remove or break legacy command behavior without coordinated Tauri changes.

---

## Rust / Tauri Conventions

**Async command arguments must be owned types:**

```rust
// CORRECT — owned String, can cross await boundary:
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }

// WRONG — &str cannot cross await boundary:
pub async fn import_folder(path: &str) -> Result<String, String> { ... }
```

**Spawn Python CLI and read stdout:**

```rust
use std::process::Command;
let output = Command::new("samplemind")
    .args(["import", &path, "--json"])
    .output()
    .map_err(|e| e.to_string())?;
let result: serde_json::Value = serde_json::from_slice(&output.stdout)?;
```

**Clippy:** `cargo clippy -- -D warnings` must pass. No suppressions without a comment.

---

## Testing

```bash
# Python tests (after Phase 2):
uv run pytest tests/ -v
uv run pytest tests/ -m "not slow"   # skip slow tests

# Rust tests:
cargo test --manifest-path app/src-tauri/Cargo.toml
```

**WAV fixtures** — never commit real audio files:

```python
# tests/conftest.py
import numpy as np, soundfile as sf, pytest
from pathlib import Path

@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path
```

**DB fixtures** — always use in-memory SQLite:

```python
@pytest.fixture
def session():
    engine = create_engine("sqlite://")  # in-memory, no file
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
```

---

## Code Safety Rules

**Never:**

## FL Studio Integration

**macOS paths:**

```
~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/  ← export target
~/Library/Audio/Plug-Ins/Components/SampleMind.component            ← AU plugin
~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3                      ← VST3 plugin
```

**macOS entitlements required** (for Tauri app + JUCE plugin):

- `com.apple.security.automation.apple-events` (AppleScript to FL Studio)
- `com.apple.security.cs.allow-unsigned-executable-memory` (Python sidecar)

**AppleScript automation** requires macOS Accessibility permission:
System Preferences → Privacy & Security → Accessibility → add the app.

---

## AI Agent Routing (2026)

This repo includes specialized phase agents under .claude/agents.

**Routing rules:**

1. If user names a phase, route to matching fase-0N agent.
2. Otherwise route to the most specific domain agent based on touched files and task intent.

**Phase agents:**

| If the task involves... | Use agent |
|---|---|
| fase 2, pytest audio fixtures, conftest, analyzer coverage, WAV test data | `fase-02-audio-testing` |
| fase 3, SQLModel, Alembic, ORM migration, repository pattern | `fase-03-database` |
| fase 4, Typer command design, Rich terminal UX, CLI JSON/stderr contract | `fase-04-cli` |
| fase 5, Flask API work, HTMX updates, SSE progress streams | `fase-05-web` |
| fase 6, Tauri commands, Rust IPC, Svelte 5 Runes desktop behavior | `fase-06-desktop` |
| fase 7, FL Studio automation, AppleScript, clipboard/MIDI handoff | `fase-07-fl-studio` |
| fase 8, JUCE plugin architecture, VST3/AU, plugin-side IPC | `fase-08-vst-plugin` |
| fase 9, sample pack format, metadata validation, distribution/versioning | `fase-09-sample-packs` |
| fase 10, production build hardening, CI/CD, signing/notarization | `fase-10-production` |

**Cross-cutting agents:**

| If the task involves... | Use agent |
|---|---|
| librosa, audio features, classifiers, WAV processing, src/analyzer/ | `audio-analyzer` |
| Tauri, Rust, Svelte 5, app/, IPC, build, macOS signing, GitHub Actions | `tauri-builder` |
| FL Studio, JUCE, VST3, AU, AppleScript, sidecar socket, plugin/ | `fl-studio-agent` |
| docs/en/, docs/no/, phase docs, ARCHITECTURE.md, CLAUDE.md, README | `doc-writer` |
| pytest, cargo test, CI failures, test fixtures, coverage, conftest.py | `test-runner` |

**Routing preference:**

1. If the request explicitly references a phase number, use the matching fase-0N agent.
2. Otherwise route to the most specific domain agent for touched files and keywords.

The agent descriptions in `.claude/agents/` contain the full trigger conditions. When in doubt between two agents, pick the one whose domain most specifically matches the task.

---

## Quick Reference

```
Phase docs:   docs/en/phase-NN-*.md
Architecture: ARCHITECTURE.md
Memory:       .claude/projects/.../memory/ (auto-loaded by Claude Code)
Skills:       .claude/commands/*.md  → /check /test /build /analyze /import /search /pack ...
Agents:       .claude/agents/*.md    → AUTOMATICALLY routed by task content (no manual invocation needed)
Copilot:      .github/copilot-instructions.md (loaded automatically by GitHub Copilot)
```
