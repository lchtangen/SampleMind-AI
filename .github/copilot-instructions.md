# GitHub Copilot - SampleMind-AI Project Instructions

SampleMind-AI is an AI-powered audio sample library manager for music producers using FL Studio.
It combines Python audio analysis, a Flask web UI, a Tauri desktop shell, and planned JUCE plugin
flows.

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
- SQLModel is a target direction, not fully live in runtime code yet

5. CI workflow is still legacy:
- .github/workflows/python-lint.yml uses Python 3.11 + pip + black + pylint
- Prefer uv + ruff for new work and propose CI migration when touching workflows

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
uv run ruff check src/
uv run ruff format src/
```

Type hints:
- Required on all new public functions/methods.

Imports:
- Prefer src-layout imports for new code:
```python
from samplemind.analyzer.audio_analysis import analyze_file
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

Preferred pattern:
```python
y, sr = librosa.load(path, sr=22050, mono=True)
rms = float(np.mean(librosa.feature.rms(y=y)))
centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)))
```

---

## Database Rules

Current runtime state:
- sqlite3 implementation is active in current code.

Target state:
- SQLModel + Alembic migration path is planned and partially scaffolded in docs.

Guideline:
- For incremental features in current runtime paths, keep sqlite3 compatibility.
- For explicit Phase 3 migration tasks, prefer SQLModel + Alembic and migrate end-to-end.

---

## Web and Desktop Rules

Flask:
- Keep API responses stable for app/src/static/app.js and desktop consumers.
- Prefer additive API changes over breaking response shape changes.

Tauri/Rust:
- Async commands must use owned input types (String, not &str).
- Return Result<T, String> and map errors with to_string().
- Register new commands in invoke_handler.

Frontend:
- If adding Svelte in app/src, use Svelte 5 Runes patterns.

Package manager for app/:
- Prefer pnpm commands for guidance and scripts.

---

## Testing and Quality

Testing rules:
1. Never commit real audio files.
2. Use synthetic WAV fixtures in tests/conftest.py.
3. Use in-memory SQLite for DB tests.

Preferred test commands:
```bash
uv run pytest tests/ -v
uv run pytest -m "not slow"
```

Lint/format rules:
- Use ruff only for Python lint and format guidance.
- Do not suggest black/flake8/pylint/isort for new workflows.

---

## Tooling and Environment

Python:
- .venv at repo root is expected.
- VS Code settings already target ${workspaceFolder}/.venv/bin/python.

Workspace commands:
- Prefer existing project scripts and tasks where available.

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

## Agent Routing (Phase + Domain)

This repo includes specialized phase agents under .claude/agents.

Phase-first routing:
- Fase 2: fase-02-audio-testing
- Fase 3: fase-03-database
- Fase 4: fase-04-cli
- Fase 5: fase-05-web
- Fase 6: fase-06-desktop
- Fase 7: fase-07-fl-studio
- Fase 8: fase-08-vst-plugin
- Fase 9: fase-09-sample-packs
- Fase 10: fase-10-production

Cross-cutting routing when no phase is explicit:
- audio-analyzer
- tauri-builder
- fl-studio-agent
- doc-writer
- test-runner

Routing rule:
1. If user names a phase, route to matching fase-0N agent.
2. Otherwise route to the most specific domain agent based on touched files and task intent.
