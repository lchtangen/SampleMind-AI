# GitHub Copilot - SampleMind-AI Project Instructions

SampleMind-AI is an AI-powered audio sample library manager for music producers using FL Studio.
It combines Python audio analysis, a Flask web UI, a Tauri 2 desktop shell, and a JUCE 8 VST3/AU plugin —
all backed by a shared SQLite database.

Primary production target: macOS 12+ Universal Binary (arm64 + x86_64)
Development environment: Windows WSL2 Ubuntu 24.04
Documentation baseline: docs/en/phase-01-foundation.md through docs/en/phase-10-production.md

---

## Current Reality Snapshot (March 2026)

Important: this repository is in a migration state with both legacy and new code paths.

1. Both legacy and src-layout code exist:
- Legacy runtime paths: src/main.py, src/analyzer, src/cli, src/data, src/web
- New package paths: src/samplemind/*

2. Desktop dev currently depends on legacy entrypoint:
- app/src-tauri/src/main.rs (debug mode) launches src/main.py serve --port 5174
- Do not break src/main.py unless app/src-tauri/src/main.rs is updated in the same change

3. Python packaging has been modernized:
- pyproject.toml + uv are active
- Python version target is >=3.13
- console script samplemind points to samplemind.cli.app:app

4. Database implementation is still sqlite3-based in current runtime code:
- src/samplemind/data/database.py currently uses sqlite3 and ~/.samplemind/library.db
- SQLModel + Alembic is the target direction, not fully live in runtime code yet

5. CI is now modernized:
- .github/workflows/python-lint.yml uses uv + ruff + pytest + clippy (updated 2026-03-25)

---

## Core Engineering Rules

1. Read the actual source file before proposing changes.
2. Respect migration state; keep compatibility unless user asks for a hard cutover.
3. Prefer minimal, safe edits over broad refactors.
4. Preserve Tauri/Python IPC contracts.
5. Prefer updating existing files over introducing new architecture layers.

---

## Python Standards

Package manager:
- Use uv only for Python dependency and execution workflows.
- Do not suggest pip install for project work.

Preferred commands:
```bash
uv sync
uv run samplemind --help
uv run pytest
uv run pytest -n auto              # parallel with pytest-xdist
uv run pytest --cov=samplemind     # coverage
uv run ruff check src/
uv run ruff format src/
```

Type hints:
- Required on all new public functions/methods.

Imports:
- Prefer src-layout imports for new code:
```python
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.analyzer.fingerprint import fingerprint_file
```

Avoid introducing:
```python
import sys; sys.path.insert(0, "src")
```

Exception for migration-safe edits:
- If touching legacy files that already rely on legacy import patterns, do not rewrite unrelated
  import architecture unless requested.

---

## CLI and IPC Contract

Use Typer for new CLI features in src/samplemind/cli.

Critical stdout/stderr split:
- JSON intended for machine consumption must go to stdout only.
- Human-readable output must go to stderr (or non-JSON mode where appropriate).

New CLI commands (2026+):
- samplemind stats [--json]              — library statistics
- samplemind duplicates [--remove]       — find/remove duplicate samples by fingerprint
- samplemind import <path> --workers N   — parallel import with N workers

Reason:
- Rust/Tauri and future sidecar flows parse stdout; mixed output breaks integration silently.

Migration safety:
- Because app/src-tauri/src/main.rs currently spawns src/main.py in debug mode,
  do not remove or break legacy command behavior without coordinated Tauri changes.

---

## Audio Analysis Rules (librosa 0.11)

1. Always use explicit sample rate for analysis code and tests.
2. Keep analysis deterministic and robust for short one-shot samples.
3. Use synthetic test fixtures (numpy + soundfile), never real audio assets in tests.
4. New features (e.g. spectral_bandwidth, fingerprinting) require a test in test_audio_analysis.py.

Preferred pattern:
```python
y, sr = librosa.load(path, sr=22050, mono=True)
rms = float(np.mean(librosa.feature.rms(y=y)))
centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)))
```

Audio fingerprinting (Phase 2+):
```python
import hashlib
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

Batch processing (Phase 2+):
```python
from concurrent.futures import ProcessPoolExecutor
import os

def analyze_batch(paths: list[Path], workers: int = 0) -> list[dict]:
    workers = workers or os.cpu_count()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(analyze_file, paths))
```

---

## Database Rules

Current runtime state:
- sqlite3 implementation is active in current code.
- WAL mode should be enabled: `PRAGMA journal_mode=WAL`
- FTS5 virtual table for search (Phase 3 target)

Target state:
- SQLModel + Alembic migration path is planned and partially scaffolded in docs.

Guideline:
- For incremental features in current runtime paths, keep sqlite3 compatibility.
- For explicit Phase 3 migration tasks, prefer SQLModel + Alembic and migrate end-to-end.

PRAGMA performance settings:
```sql
PRAGMA journal_mode=WAL;
PRAGMA cache_size = -64000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
```

---

## Web and Desktop Rules

Flask:
- Keep API responses stable for app/src/static/app.js and desktop consumers.
- Prefer additive API changes over breaking response shape changes.
- Add flask-cors for Tauri WebView: `CORS(app, origins=["tauri://localhost"])`

New endpoints (2026+):
- `POST /api/samples/bulk-tag` — bulk tag by ID list
- `GET /api/import/progress` — SSE stream for import progress
- `GET /api/samples/stats` — library statistics

Tauri/Rust:
- Async commands must use owned input types (String, not &str).
- Return Result<T, String> and map errors with to_string().
- Register new commands in invoke_handler AND capabilities JSON.

New Tauri features (2026+):
- tauri-plugin-notification: import complete notifications
- tauri-plugin-deep-link: samplemind://import?path=... URL scheme
- tauri-plugin-updater: auto-updater via GitHub Releases

Frontend:
- If adding Svelte in app/src, use Svelte 5 Runes patterns.
- SearchBar component: `let query = $state(''); let results = $derived.by(...)`

Package manager for app/:
- Prefer pnpm commands for guidance and scripts.

---

## Testing and Quality

Testing rules:
1. Never commit real audio files.
2. Use synthetic WAV fixtures in tests/conftest.py.
3. Use in-memory SQLite for DB tests.
4. Coverage targets: analyzer 80%+, classifier 90%+, CLI 70%+

Preferred test commands:
```bash
uv run pytest tests/ -v
uv run pytest -m "not slow"
uv run pytest -n auto                        # parallel execution
uv run pytest --cov=samplemind --cov-report=term-missing  # coverage
```

Test markers:
```python
@pytest.mark.slow      # tests taking >1 second (audio analysis)
@pytest.mark.macos     # requires macOS (AppleScript, AU validation)
@pytest.mark.juce      # requires JUCE plugin to be built
```

CI matrix (target ci.yml):
- Python 3.13 on ubuntu-latest
- Python 3.13 on macos-latest
- Rust clippy + cargo test on ubuntu-latest

Lint/format rules:
- Use ruff only for Python lint and format guidance.
- Do not suggest black/flake8/pylint/isort for new workflows.

---

## Tooling and Environment

Python:
- .venv at repo root is expected.
- VS Code settings already target ${workspaceFolder}/.venv/bin/python.
- pre-commit hooks: ruff check + ruff format on staged files

WSL2 performance:
- Always develop on Linux filesystem (/home/ubuntu/...), not /mnt/c/
- Enable git fsmonitor: `git config core.fsmonitor true`

File path handling:
- Prefer platformdirs for new cross-platform config/data locations.
- Avoid introducing new hardcoded home-directory paths in new code.

---

## What Not to Suggest

- pip install for project dependency management
- python -m venv as primary workflow
- black, flake8, pylint, isort as the default lint stack
- npm in app/ when pnpm is the project standard
- sys.path.insert hacks in new code
- committing real audio fixtures
- breaking legacy src/main.py runtime contract without coordinated Tauri update
- hardcoded home directory paths (use platformdirs)
- raw TCP sockets for sidecar IPC (use Unix domain socket)

---

## FL Studio Context

SampleMind integrates with FL Studio via:
1. Filesystem export (simplest — copy WAVs to FL Studio Samples folder)
2. Clipboard paths (pbcopy on macOS, clip.exe on Windows)
3. AppleScript automation on macOS (focus FL Studio, open sample browser F8)
4. Windows COM automation (win32com.client for Windows)
5. Virtual MIDI (IAC Driver on macOS, CC messages for BPM/key metadata)
6. JUCE VST3/AU plugin (full integration — live sample browser inside FL Studio)

Assume macOS-first behavior for FL Studio automation unless user explicitly targets Windows.

FL Studio 21 macOS paths:
```
~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/
```

FL Studio 21 Windows paths:
```
C:\Users\<name>\Documents\Image-Line\FL Studio 21\Data\Patches\Samples\SampleMind\
```

---

## Security Rules (2026-2028)

1. No network access required — SampleMind is fully local
2. macOS sandbox entitlements: use minimum required set only
3. Sidecar binary: verify SHA-256 checksum at startup before execution
4. Code signing: Apple Developer ID (macOS), Azure Trusted Signing (Windows)
5. No telemetry without explicit opt-in (SAMPLEMIND_SENTRY_DSN env var)
6. Audio files never copied without explicit user action
7. SQLite database is plain user-owned file — no encryption required
8. No credentials, tokens, or API keys stored in the database or config

---

## Observability Rules (2026-2028)

1. Python logging: always to stderr, never stdout (preserves IPC contract)
2. Log structured data at DEBUG level: `{"event": "analyze", "path": ..., "duration_ms": ...}`
3. Sentry opt-in: `if os.getenv("SAMPLEMIND_SENTRY_DSN"): sentry_sdk.init(...)`
4. Performance logging: log analysis time, import batch time at DEBUG level
5. Tauri: use `tauri::api::log` for Rust-side logging
6. Never log audio file contents or user file paths at INFO+ level (privacy)

---

## Agent Routing (Phase + Domain)

This repo includes specialized phase agents under .claude/agents.

Phase-first routing:
- Phase 2: phase-02-audio-testing
- Phase 3: phase-03-database
- Phase 4: phase-04-cli
- Phase 5: phase-05-web
- Phase 6: phase-06-desktop
- Phase 7: phase-07-fl-studio
- Phase 8: phase-08-vst-plugin
- Phase 9: phase-09-sample-packs
- Phase 10: phase-10-production

Cross-cutting routing when no phase is explicit:
- audio-analyzer (librosa, features, fingerprinting, batch)
- tauri-builder (Rust, Tauri, Svelte 5, notifications, deep-link, updater)
- fl-studio-agent (FL Studio, JUCE, sidecar, AppleScript, MIDI)
- doc-writer (docs, ARCHITECTURE.md, CLAUDE.md, README)
- test-runner (pytest, coverage, xdist, CI matrix)

Routing rule:
1. If user names a phase, route to matching phase-0N agent.
2. Otherwise route to the most specific domain agent based on touched files and task intent.
