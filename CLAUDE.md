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
| `.github/workflows/` | CI/CD: ci.yml (uv+ruff+pytest+clippy) |

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
| CI | ci.yml (uv+ruff+pytest+clippy) | (live) |
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
# --- Python (legacy — still needed for Tauri dev mode) ---
source .venv/bin/activate
python src/main.py list
python src/web/app.py              # Flask at http://localhost:5000

# --- Python (uv — use for all new work) ---
uv sync                            # install deps
uv run samplemind list
uv run samplemind serve
uv run pytest tests/ -v
uv run pytest tests/test_audio_analysis.py::test_bpm -v  # single test
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

**Audio analysis canonical pattern:**

```python
y, sr = librosa.load(path, sr=22050, mono=True)   # always explicit sr
rms = float(np.mean(librosa.feature.rms(y=y)))
centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)))
```

**Audio fingerprinting** (SHA-256 of first 64 KB — for deduplication):

```python
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

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

**Coverage targets:** analyzer 80%+, classifier 90%+, CLI 70%+.

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

This repo includes specialized phase agents under .claude/agents.

**Routing rules:**

1. If user names a phase, route to matching phase-0N agent.
2. Otherwise route to the most specific domain agent based on touched files and task intent.

**Phase agents:**

| If the task involves... | Use agent |
|---|---|
| phase 2, pytest audio fixtures, conftest, analyzer coverage, WAV test data | `phase-02-audio-testing` |
| phase 3, SQLModel, Alembic, ORM migration, repository pattern | `phase-03-database` |
| phase 4, Typer command design, Rich terminal UX, CLI JSON/stderr contract | `phase-04-cli` |
| phase 5, Flask API work, HTMX updates, SSE progress streams | `phase-05-web` |
| phase 6, Tauri commands, Rust IPC, Svelte 5 Runes desktop behavior | `phase-06-desktop` |
| phase 7, FL Studio automation, AppleScript, clipboard/MIDI handoff | `phase-07-fl-studio` |
| phase 8, JUCE plugin architecture, VST3/AU, plugin-side IPC | `phase-08-vst-plugin` |
| phase 9, sample pack format, metadata validation, distribution/versioning | `phase-09-sample-packs` |
| phase 10, production build hardening, CI/CD, signing/notarization | `phase-10-production` |

**Cross-cutting agents:**

| If the task involves... | Use agent |
|---|---|
| librosa, audio features, classifiers, WAV processing, fingerprinting, batch analysis | `audio-analyzer` |
| Tauri, Rust, Svelte 5, app/, IPC, build, macOS signing, GitHub Actions | `tauri-builder` |
| FL Studio, JUCE, VST3, AU, AppleScript, sidecar socket, plugin/ | `fl-studio-agent` |
| docs/en/, docs/no/, phase docs, ARCHITECTURE.md, CLAUDE.md, README | `doc-writer` |
| pytest, cargo test, CI failures, test fixtures, coverage, conftest.py | `test-runner` |

**Routing preference:**

1. If the request explicitly references a phase number, use the matching phase-0N agent.
2. Otherwise route to the most specific domain agent for touched files and keywords.

---

## Database Rules

**Current runtime:** sqlite3 implementation is active.
**Target:** SQLModel + Alembic migration path is planned and partially scaffolded in docs.

Guideline:

- Current DB file: `~/.samplemind/library.db`
  (platformdirs target: `~/Library/Application Support/SampleMind/samplemind.db` on macOS).
- For incremental features in current runtime paths, keep sqlite3 compatibility.
- For explicit Phase 3 migration tasks, prefer SQLModel + Alembic and migrate end-to-end.
- New database features (WAL mode, FTS5, backup): implement in `src/samplemind/data/database.py`

**PRAGMA settings** (apply on connection open for performance):

```sql
PRAGMA journal_mode=WAL;
PRAGMA cache_size = -64000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
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
Skills:       .claude/commands/*.md  → /check /test /build /analyze /import /search /pack ...
Agents:       .claude/agents/*.md    → AUTOMATICALLY routed by task content (no manual invocation needed)
Copilot:      .github/copilot-instructions.md (loaded automatically by GitHub Copilot)
```
