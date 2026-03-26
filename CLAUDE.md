# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## SampleMind-AI — Claude Code Project Guide (2026)

> AI-powered audio sample library manager for FL Studio (macOS primary, Windows secondary).
> Development: Windows WSL2. Production: macOS 12+ Universal Binary.

---

## Core Engineering Rules

1. **Read the actual source file before proposing changes.**
2. **Respect migration state; keep compatibility unless user asks for a hard cutover.**
3. **Prefer minimal, safe edits over broad refactors.**
4. **Preserve Tauri/Python IPC contracts.**
5. **Prefer updating existing files over introducing new architecture layers.**

---

## Project Overview

SampleMind-AI analyzes WAV/AIFF sample files with librosa (BPM, key, instrument, mood, energy),
stores metadata in SQLite, and surfaces everything through a CLI, Flask web UI, Tauri desktop app,
and JUCE VST3/AU plugin — all reading the same database.

**Key docs:**

- [ARCHITECTURE.md](../ARCHITECTURE.md) — system diagram, IPC contract table
- [docs/en/phase-01-foundation.md](../docs/en/phase-01-foundation.md) through [docs/en/phase-10-production.md](../docs/en/phase-10-production.md) — phase upgrade path

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
| `.github/workflows/` | CI/CD: ci.yml (uv+ruff+pytest+clippy) |

---

## Migration State (2026)

| Component | Current | Target |
|---|---|---|
| Package manager | uv + pyproject.toml | ✅ live |
| Python version | 3.13 | ✅ live |
| Package layout | src/samplemind/ | ✅ live |
| CLI | Typer (src/samplemind/cli/app.py) — 8 commands | ✅ live |
| Database | SQLModel + Alembic (data/orm.py + migrations/) | ✅ live |
| Auth | JWT + RBAC (core/auth/ + api/routes/auth.py) | ✅ live |
| Repositories | SampleRepository + UserRepository | ✅ live |
| Lint/format | ruff ≥0.15 | ✅ live |
| Type checking | pyright ≥1.1.390 | ✅ live |
| Tests | pytest ≥9 + hypothesis + soundfile fixtures (33 tests) | ✅ live |
| CI | ruff + pyright + pytest + alembic check + clippy | ✅ live |
| Frontend | Svelte 5 Runes + Vite | 📋 Phase 7 |
| Plugin | JUCE 8 VST3/AU | 📋 Phase 9 |

**Important:**

- **Legacy database.py still exists** in `src/samplemind/data/database.py`. It is still imported by
  `src/samplemind/api/main.py` and `src/samplemind/cli/commands/serve.py` (both call `init_db()` for
  backward compatibility). Phase 5 cleanup will remove these remaining call sites and delete
  `database.py` entirely. Do not add new code that imports from it.
- **src/main.py** (legacy argparse entry point) is still required for Tauri dev mode. Do not remove it unless you also update `app/src-tauri/src/main.rs`.
- The active runtime uses `init_orm()` (not `init_db()`), `SampleRepository` (not `save_sample()` / `search_samples()`), and `get_session()` (not `_connect()`).

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

# Speed up git on WSL2:
git config core.fsmonitor true
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
# --- Python (uv — use for all work) ---
uv sync --dev                      # install all deps + dev tools into .venv
uv run alembic upgrade head        # apply all schema migrations (required before first run)
uv run samplemind --help           # show all 8 commands

uv run samplemind import ~/Music/  # import + analyze WAV files
uv run samplemind list             # list library in a Rich table
uv run samplemind search --query "dark" --energy high  # filter search
uv run samplemind tag "kick_128" --genre trap          # manual tag
uv run samplemind serve            # Flask web UI at http://localhost:5000
uv run samplemind api              # FastAPI auth server at http://localhost:8000/docs

uv run pytest tests/ -v                                          # run all 33 tests
uv run pytest tests/ -v -m "not slow"                           # fast tests only
uv run pytest tests/test_audio_analysis.py::test_bpm -v         # single test
uv run ruff check src/ tests/                                    # lint
uv run ruff format src/ tests/                                   # format
uv run pyright src/                                              # type-check
uv run alembic check                                             # verify no migration drift

# --- Python (legacy entry point — do not use for new work) ---
# src/main.py is the legacy argparse CLI still used by Tauri dev mode.
# Do not break it; do not add features to it.
python src/main.py list            # legacy only

# --- Tauri desktop app ---
cd app && pnpm install
pnpm tauri dev                     # dev mode (spawns Flask on port 5174)
pnpm tauri build                   # production bundle

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

**Audio analysis canonical pattern** (matches `src/samplemind/analyzer/audio_analysis.py`):

```python
y, sr = librosa.load(path)                              # default sr=22050, soxr_hq resampling
rms = float(np.sqrt(np.mean(y ** 2)))                   # NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized to 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
```

**Classifier output values** (exact strings stored in DB — never use alternatives):

| Field | Valid values |
|-------|-------------|
| `energy` | `"low"` `"mid"` `"high"` — ⚠️ **never `"medium"`** |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` |

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
# Python tests:
uv run pytest tests/ -v
uv run pytest tests/test_audio_analysis.py::test_bpm -v  # single test
uv run pytest tests/ -m "not slow"   # skip slow tests
uv run pytest tests/ -n auto          # parallel with pytest-xdist
uv run pytest --cov=samplemind --cov-report=term-missing  # coverage

# Rust tests:
cargo test --manifest-path app/src-tauri/Cargo.toml
```

**Test markers:**

```python
@pytest.mark.slow    # tests > 1s (audio analysis) — skipped in fast CI runs
@pytest.mark.macos   # requires macOS (AppleScript, AU validation)
@pytest.mark.juce    # requires JUCE plugin to be built
```

**Coverage minimum (CI-enforced):** 60% overall — configured in `[tool.coverage.report]` in
`pyproject.toml` and enforced by the CI `python` job (no `continue-on-error`).
**Coverage aspirational targets:** analyzer 80%+, classifier 90%+, CLI 70%+.

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

@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    """Simulated kick: high amplitude, low frequency."""
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path

@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    """Simulated hihat: white noise, short."""
    samples = np.random.uniform(-0.3, 0.3, 2205).astype(np.float32)  # 0.1s
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path
```

---

## Code Safety Rules

**Never:**

1. Commit real audio files (WAV, AIFF, MP3, FLAC) — generate synthetic fixtures
2. Hardcode home directory paths — use `platformdirs`
3. Print JSON to stderr or human text to stdout — keep IPC contract clean
4. Add `sys.path.insert` hacks in new code
5. Use `pip install` or `python -m venv` in new documentation or scripts
6. Break `src/main.py` entrypoint without a coordinated Tauri update
7. Suggest `black`, `flake8`, `pylint`, `isort` — use `ruff` only
8. Use `npm` in `app/` — use `pnpm`
9. Skip `cargo clippy` warnings — fix them
10. Commit `.env` files or credentials

**2026-2028 forward rules:**

11. All new Python modules must have type annotations on public functions
12. New Tauri commands must be registered in both `invoke_handler` and the capability JSON
13. All new database schema changes must have an Alembic migration
14. New CLI commands must output JSON to stdout when `--json` flag is passed
15. New audio features must have a corresponding pytest fixture and test
16. Sidecar socket protocol changes must be versioned (add `"version": 2` to JSON envelope)

---

## FL Studio Integration

**macOS paths (FL Studio 20/21):**

```
~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/       ← FL Studio 20
~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/    ← FL Studio 21
~/Library/Audio/Plug-Ins/Components/SampleMind.component                  ← AU plugin
~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3                            ← VST3 plugin
```

**Windows paths:**

```
C:\Users\<name>\Documents\Image-Line\FL Studio\Data\Patches\Samples\SampleMind\
C:\Users\<name>\Documents\Image-Line\FL Studio 21\Data\Patches\Samples\SampleMind\
```

**macOS entitlements required** (for Tauri app + JUCE plugin):

- `com.apple.security.automation.apple-events` (AppleScript to FL Studio)
- `com.apple.security.cs.allow-unsigned-executable-memory` (Python sidecar)
- `com.apple.security.files.user-selected.read-write` (file access)
- `com.apple.security.assets.music.read-write` (Music folder access)

**AppleScript automation** requires macOS Accessibility permission:
System Preferences → Privacy & Security → Accessibility → add the app.

---

## AI Agent Routing (2026)

This repo has **24 specialized agents** in `.claude/agents/` that activate automatically.
Agents are triggered by three signals — in priority order:

1. **Open file path** — the file being edited matches an agent's file glob patterns
2. **Code content** — symbols/imports visible in the active file match an agent's code patterns
3. **Chat keywords** — what the user types matches an agent's description keywords

> The full routing table is mirrored in `.auggie/routing.yaml` and `.auggie/agents.yaml`.

**Routing priority:**
1. Phase number mentioned → matching `phase-0N` agent
2. Open file path match → agent that owns that file
3. Code pattern match → agent that owns that symbol
4. Chat keyword match → most specific domain agent

---

## File-Based Agent Auto-Routing

Claude Code reads each agent's `description` field and activates the matching agent
when the open file, visible code, or chat message contains any of its trigger patterns.
This table is the **canonical reference** — it mirrors `.auggie/routing.yaml` exactly.

### File Path → Agent

| File glob pattern | Auto-activates agent |
|---|---|
| `src/samplemind/analyzer/**/*.py` | `audio-analyzer` |
| `src/analyzer/**/*.py` | `audio-analyzer` |
| `tests/test_audio_analysis.py` | `audio-analyzer` |
| `tests/test_classifier.py` | `audio-analyzer` |
| `tests/test_fingerprint.py` | `audio-analyzer` |
| `tests/conftest.py` | `phase-02-audio-testing` |
| `tests/test_*.py` | `test-runner` |
| `tests/**/*.py` | `test-runner` |
| `src/samplemind/api/**/*.py` | `api-agent` |
| `src/samplemind/core/auth/**/*.py` | `security-agent` |
| `src/samplemind/core/models/user.py` | `security-agent` |
| `src/samplemind/web/app.py` | `web-agent` |
| `src/web/app.py` | `web-agent` |
| `src/samplemind/web/templates/**/*.html` | `web-agent` |
| `src/samplemind/web/static/**` | `web-agent` |
| `src/samplemind/cli/**/*.py` | `phase-04-cli` |
| `src/main.py` | `phase-04-cli` |
| `src/samplemind/data/**/*.py` | `phase-03-database` |
| `src/samplemind/core/models/sample.py` | `phase-03-database` |
| `migrations/**/*.py` | `phase-03-database` |
| `alembic.ini` | `phase-03-database` |
| `app/src-tauri/src/**/*.rs` | `tauri-builder` |
| `app/src-tauri/Cargo.toml` | `tauri-builder` |
| `app/src-tauri/tauri.conf.json` | `tauri-builder` |
| `app/src-tauri/capabilities/**/*.json` | `tauri-builder` |
| `app/src/**/*.svelte` | `phase-06-desktop` |
| `app/src/**/*.ts` | `phase-06-desktop` |
| `app/src-tauri/entitlements.plist` | `phase-10-production` |
| `plugin/Source/**/*.cpp` | `phase-08-vst-plugin` |
| `plugin/Source/**/*.h` | `phase-08-vst-plugin` |
| `plugin/CMakeLists.txt` | `phase-08-vst-plugin` |
| `src/samplemind/sidecar/**/*.py` | `fl-studio-agent` |
| `src/samplemind/integrations/**/*.py` | `fl-studio-agent` |
| `src/samplemind/packs/**/*.py` | `phase-09-sample-packs` |
| `src/samplemind/search/**/*.py` | `phase-11-semantic-search` |
| `src/samplemind/agent/**/*.py` | `phase-12-ai-curation` |
| `src/samplemind/sync/**/*.py` | `phase-13-cloud-sync` |
| `src/samplemind/analytics/**/*.py` | `phase-14-analytics` |
| `src/samplemind/marketplace/**/*.py` | `phase-15-marketplace` |
| `src/samplemind/generation/**/*.py` | `phase-16-ai-generation` |
| `src/samplemind/utils/model_loader.py` | `ml-agent` |
| `scripts/**/*.sh` | `devops-agent` |
| `.github/workflows/*.yml` | `devops-agent` |
| `.github/workflows/release.yml` | `phase-10-production` |
| `pyproject.toml` | `devops-agent` |
| `.pre-commit-config.yaml` | `devops-agent` |
| `docs/en/**/*.md` | `doc-writer` |
| `docs/no/**/*.md` | `doc-writer` |
| `ARCHITECTURE.md`, `README.md`, `CONTRIBUTING.md` | `doc-writer` |

### Code Pattern → Agent

| Symbol / import visible in file | Auto-activates agent |
|---|---|
| `librosa.load`, `classify_energy`, `classify_instrument`, `fingerprint_file`, `spectral_centroid` | `audio-analyzer` |
| `from fastapi import`, `APIRouter`, `@router.get`, `Depends(get_current_active_user` | `api-agent` |
| `from flask import`, `@app.route`, `render_template(`, `hx-get=`, `text/event-stream` | `web-agent` |
| `from jose import jwt`, `CryptContext`, `RBACService`, `UserRole`, `SAMPLEMIND_SECRET_KEY` | `security-agent` |
| `#[tauri::command]`, `use tauri::`, `invoke(` | `tauri-builder` |
| `$state(`, `$derived(`, `$effect(` | `phase-06-desktop` |
| `@pytest.fixture`, `def test_`, `import pytest` | `test-runner` |
| `sf.write(`, `kick_wav`, `hihat_wav`, `np.sin(2 * np.pi` | `phase-02-audio-testing` |
| `from sqlmodel import`, `PRAGMA journal_mode`, `alembic revision` | `phase-03-database` |
| `import typer`, `typer.Typer()`, `@app.command()` | `phase-04-cli` |
| `juce::`, `#include <juce_audio_processors` | `phase-08-vst-plugin` |
| `from transformers import`, `AutoModelForCausalLM`, `load_in_8bit=True` | `ml-agent` |
| `import faiss`, `CLAP`, `embed_audio`, `embed_text`, `VectorIndex` | `phase-11-semantic-search` |
| `import litellm`, `analyze_library`, `curate(`, `playlist_by_energy` | `phase-12-ai-curation` |
| `import boto3`, `s3.head_object`, `SyncSettings`, `push_metadata` | `phase-13-cloud-sync` |
| `import plotly`, `bpm_histogram_chart`, `get_key_heatmap`, `get_summary` | `phase-14-analytics` |
| `stripe.checkout`, `PackListing`, `validate_pack_for_marketplace` | `phase-15-marketplace` |
| `from audiocraft`, `StableAudioPipeline`, `GenerationRequest`, `MODEL_REGISTRY` | `phase-16-ai-generation` |
| `osascript`, `IAC Driver`, `win32com.client`, `nc -U /tmp/samplemind.sock` | `fl-studio-agent` |
| `uv sync`, `astral-sh/setup-uv`, `runs-on: ubuntu`, `#!/usr/bin/env bash` | `devops-agent` |
| `xcrun notarytool`, `codesign`, `APPLE_SIGNING_IDENTITY`, `universal-apple-darwin` | `phase-10-production` |

### Chat Keyword → Agent

| Keyword or phrase | Auto-activates agent |
|---|---|
| librosa, BPM, WAV, audio analysis, classify, fingerprint, spectral | `audio-analyzer` |
| pytest, test, failing, coverage, CI, conftest, fixture | `test-runner` |
| Tauri, Rust, Svelte, build the app, pnpm tauri, cargo | `tauri-builder` |
| FastAPI, REST API, /api/v1, endpoint, OpenAPI, Bearer token | `api-agent` |
| Flask, web UI, HTMX, SSE, login page, audio streaming | `web-agent` |
| JWT, RBAC, permission, role, bcrypt, OAuth2, secure this endpoint | `security-agent` |
| setup, CI/CD, GitHub Actions, WSL2, environment, install | `devops-agent` |
| ML model, transformers, HuggingFace, embedding | `ml-agent` |
| CLAP, FAISS, vector index, cosine similarity, semantic search | `phase-11-semantic-search` |
| curate, LiteLLM, energy arc, gap analysis, smart playlist | `phase-12-ai-curation` |
| cloud sync, R2, Supabase, multi-device, sync push/pull | `phase-13-cloud-sync` |
| analytics, Plotly, BPM histogram, key heatmap, growth timeline | `phase-14-analytics` |
| marketplace, Stripe, pack publishing, signed URL, CDN | `phase-15-marketplace` |
| generate sample, AudioCraft, Stable Audio, text-to-audio | `phase-16-ai-generation` |
| document, write a doc, update README, phase doc, ARCHITECTURE | `doc-writer` |
| FL Studio, JUCE, VST3, AU, sidecar, MIDI, AppleScript | `fl-studio-agent` |
| Phase 2 | `phase-02-audio-testing` |
| Phase 3 | `phase-03-database` |
| Phase 4 | `phase-04-cli` |
| Phase 5 | `web-agent` |
| Phase 6 | `phase-06-desktop` |
| Phase 7 | `fl-studio-agent` |
| Phase 8 | `phase-08-vst-plugin` |
| Phase 9 | `phase-09-sample-packs` |
| Phase 10 | `phase-10-production` |
| Phase 11 | `phase-11-semantic-search` |
| Phase 12 | `phase-12-ai-curation` |
| Phase 13 | `phase-13-cloud-sync` |
| Phase 14 | `phase-14-analytics` |
| Phase 15 | `phase-15-marketplace` |
| Phase 16 | `phase-16-ai-generation` |

---

## Database Rules

**Current runtime:** SQLModel + Alembic — fully live as of Phase 4 (v0.2.0).
The legacy `data/database.py` (sqlite3) is no longer used by any command or web route.

Guidelines:

- **DB file location:** determined by `get_settings().database_url` which uses `platformdirs`: `~/Library/Application Support/SampleMind/samplemind.db` on macOS; `%LOCALAPPDATA%\SampleMind\samplemind.db` on Windows.
- **Never use raw sqlite3** for new code. Use `SampleRepository` or `UserRepository` which call `get_session()` internally.
- **Never import from `data/database.py`** in new code. Remove import sites as they are encountered.
- **Schema changes require a migration**: create a new file in `migrations/versions/` and run `uv run alembic upgrade head`. CI runs `alembic check` to catch drift.
- **FTS5 virtual table**: not yet added — planned for Phase 5. Current search uses `WHERE ... LIKE` via SQLModel.

**WAL + PRAGMA settings** are applied automatically on every new connection via a SQLAlchemy event listener in `data/orm.py`. You do not need to set them manually:

```python
# src/samplemind/data/orm.py — applied to every new SQLite connection
def _apply_sqlite_pragmas(dbapi_conn, _connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")       # concurrent readers during writes
    cursor.execute("PRAGMA cache_size=-64000")      # 64 MB page cache (negative = KB)
    cursor.execute("PRAGMA synchronous=NORMAL")     # safe + fast (not FULL)
    cursor.execute("PRAGMA temp_store=MEMORY")      # in-RAM temp tables and indexes
    cursor.execute("PRAGMA mmap_size=268435456")    # 256 MB memory-mapped I/O
    cursor.close()
```

**Using SampleRepository in new code:**

```python
# Always use the repository; never open a raw sqlite3 connection in CLI/web/API code.
from samplemind.core.models.sample import SampleCreate, SampleUpdate
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.data.orm import init_orm

# Call init_orm() once at startup (idempotent — safe to call multiple times).
# It imports all models and calls SQLModel.metadata.create_all(engine).
init_orm()

# Insert or update a sample (auto-detected fields only; genre/tags never overwritten):
sample = SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/abs/path/kick.wav", bpm=128.0))

# Search by any combination of filters (all parameters are optional):
results = SampleRepository.search(query="dark", energy="high", instrument="kick")

# Update user-defined tags (only non-None fields are written):
SampleRepository.tag("/abs/path/kick.wav", SampleUpdate(genre="trap", tags="808,heavy"))
```

---

## Web and Desktop Rules

**Flask:**

- Keep API responses stable for app/src/static/app.js and desktop consumers.
- Prefer additive API changes over breaking response shape changes.
- Add `flask-cors` for Tauri WebView cross-origin requests.

**Tauri/Rust:**

- Async commands must use owned input types (String, not &str).
- Return Result<T, String> and map errors with to_string().
- Register new commands in invoke_handler AND in capabilities JSON.

**Frontend:**

- If adding Svelte in app/src, use Svelte 5 Runes patterns.

**Package manager for app/:**

- Prefer pnpm commands for guidance and scripts.

---

## Quick Reference

```
Phase docs:   docs/en/phase-NN-*.md
Architecture: ARCHITECTURE.md
Memory:       .claude/projects/.../memory/ (auto-loaded by Claude Code)

Claude Code agents (24 total — auto-activated by file, code, or keyword):
  Domain:  audio-analyzer  test-runner  tauri-builder  doc-writer  fl-studio-agent
           api-agent  web-agent  security-agent  devops-agent  ml-agent
  Phase:   phase-01-foundation  phase-02-audio-testing  phase-03-database  phase-04-cli
           phase-06-desktop  phase-08-vst-plugin  phase-09-sample-packs  phase-10-production
           phase-11-semantic-search  phase-12-ai-curation  phase-13-cloud-sync
           phase-14-analytics  phase-15-marketplace  phase-16-ai-generation

Claude Code commands (13 total — type /command in chat):
  /analyze   /import    /search    /check     /test      /build
  /serve     /start     /list      /tag       /health    /db-inspect
  /auth      /setup     /debug     /workflow  /pack      /sidecar

Auggie CLI skills (22 total):
  analyze_audio  batch_import  build  check  coverage  db_inspect  db_migrate
  fingerprint  health_check  import_samples  lint  list_samples  pack  run_tests
  search  serve_api  serve_web  setup_dev  sidecar  start  auth  tag

Auggie CLI workflows (7 total):
  ci-check  new-feature  release  dev-start  debug-classifier
  add-audio-feature  onboard-dev

GitHub Copilot agents (9 total — @mention in Copilot Chat):
  @audio-analyzer  @test-runner  @tauri-builder  @fl-studio-agent  @document-creator
  @api-agent  @web-agent  @security-agent  @devops-agent  @ml-agent

Copilot:  .github/copilot-instructions.md (loaded automatically by GitHub Copilot)
```
