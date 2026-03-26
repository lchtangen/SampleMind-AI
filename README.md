# SampleMind AI

> AI-powered audio sample library manager for FL Studio producers.
> Analyze, tag, search, and export your sample library — from the CLI, web UI, desktop app, or VST3/AU plugin.

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Tauri 2](https://img.shields.io/badge/tauri-2-yellow.svg)](https://tauri.app/)
[![JUCE 8](https://img.shields.io/badge/JUCE-8-orange.svg)](https://juce.com/)
[![uv](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/badge/lint-ruff-brightgreen.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

---

## What It Does

SampleMind AI analyzes your WAV and AIFF sample files using [librosa](https://librosa.org/), stores metadata in a local SQLite database, and gives you multiple ways to browse and work with your library:

- **CLI** — 21 commands: `import`, `search`, `generate`, `curate`, `similar`, `pack`, `sync`, `analytics` and more
- **Web UI** — Flask + HTMX browser interface with waveform preview and SSE progress
- **Desktop App** — Tauri 2 + Svelte 5 native app (macOS .dmg, Windows .msi)
- **VST3/AU Plugin** — Live sample browser inside FL Studio (JUCE 8, PythonSidecar IPC)

Everything reads from the same SQLite database — no sync needed.

---

## Features

| Feature | Description |
|---------|-------------|
| **8-Feature Audio Analysis** | BPM, key, instrument, mood, energy, duration, spectral features |
| **AI Classification** | Automatic: kick/snare/hihat/bass/pad/lead/loop/sfx + dark/chill/aggressive/euphoric/melancholic/neutral + low/mid/high |
| **Audio Fingerprinting** | SHA-256 dedup detection — find and remove exact duplicates |
| **Batch Import** | Parallel analysis with `--workers` (defaults to CPU count) |
| **SQLite Library** | WAL mode + FTS5 full-text search, < 50ms queries |
| **Semantic Search** | CLAP audio embeddings + sqlite-vec — search by sound similarity or text description |
| **AI Curation** | pydantic-ai smart playlists, energy arc generation, gap analysis via LiteLLM |
| **AI Generation** | Text-to-audio via AudioCraft MusicGen/AudioGen or Stable Audio Open |
| **FL Studio Export** | Filesystem copy, clipboard path, AppleScript, MIDI metadata |
| **Sample Packs** | Export/import `.smpack` bundles with SHA-256 integrity |
| **Cloud Sync** | R2/S3 file sync + Supabase metadata sync across devices |
| **Analytics** | Plotly BPM histograms, key heatmaps, mood/energy breakdowns |
| **Auto-Updater** | Sparkle (macOS) / NSIS (Windows) via GitHub Releases |
| **Offline-First** | Fully local — no cloud, no API keys required for core features |

---

## Quick Start (WSL2 / macOS)

### Prerequisites

```bash
# Install uv (Rust-based Python package manager):
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo:
git clone https://github.com/lchtangen/SampleMind-AI.git
cd SampleMind-AI
```

### Install & Run

```bash
# Install all dependencies including dev tools (creates .venv automatically):
uv sync --dev

# Run the database migrations to create the SQLite tables (required before first run):
uv run alembic upgrade head

# Run the CLI:
uv run samplemind --help

# Import a folder of WAV samples (analyzes BPM, key, instrument, mood, energy):
uv run samplemind import ~/Music/Samples/

# List all imported samples in a table:
uv run samplemind list

# Search the library (text query, combined with optional filters):
uv run samplemind search --query "dark kick" --energy high

# Tag a sample with genre and custom tags:
uv run samplemind tag "kick_128" --genre trap --tags "808,heavy"

# Start the web UI (http://localhost:5000):
uv run samplemind serve

# Start the FastAPI auth server (http://localhost:8000/docs for OpenAPI UI):
uv run samplemind api
```

### Development Setup (WSL2)

```bash
# Run the full test suite (262 tests):
uv run pytest tests/ -v

# Run only fast tests (skips real librosa analysis — ~0.5s total):
uv run pytest tests/ -v -m "not slow"

# Lint and type-check:
uv run ruff check src/ tests/
uv run pyright src/

# Run full CI suite locally (same checks as GitHub Actions):
uv run ruff check src/ tests/ && uv run pyright src/ && uv run pytest tests/ -n auto && uv run alembic check
```

---

## macOS Production Build

```bash
# Prerequisites:
xcode-select --install
brew install uv pnpm rustup
rustup target add aarch64-apple-darwin x86_64-apple-darwin

# Build Python package:
uv build

# Build PyInstaller sidecar:
uv run pyinstaller samplemind-sidecar.spec --noconfirm

# Build Universal Binary desktop app (arm64 + x86_64):
cd app && pnpm install
pnpm tauri build --target universal-apple-darwin

# Verify Universal Binary:
lipo -info app/src-tauri/target/universal-apple-darwin/release/bundle/macos/SampleMind.app/Contents/MacOS/SampleMind
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Package manager** | [uv](https://github.com/astral-sh/uv) | Fast Python deps, replaces pip/venv |
| **Python** | 3.13 | Core analysis + CLI + web backend |
| **Audio analysis** | [librosa 0.11](https://librosa.org/) | Feature extraction (8 features per file) |
| **Database** | SQLite (WAL + FTS5) | Local sample metadata store |
| **ORM** | SQLModel + Alembic | Type-safe DB layer; versioned schema migrations |
| **Auth** | JWT (python-jose) + bcrypt | Access + refresh tokens; viewer/owner/admin RBAC |
| **API** | FastAPI + Uvicorn | Async REST API with auto-generated OpenAPI docs |
| **CLI** | [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) | Beautiful terminal UX with `--json` output for IPC |
| **Web UI** | Flask + [HTMX](https://htmx.org/) | Browser interface, SSE progress |
| **Desktop app** | [Tauri 2](https://tauri.app/) | Native macOS/Windows app (~15 MB) |
| **Frontend** | [Svelte 5](https://svelte.dev/) Runes + Vite | Reactive desktop UI |
| **Plugin** | [JUCE 8](https://juce.com/) | VST3/AU plugin for FL Studio |
| **Lint/format** | [ruff](https://github.com/astral-sh/ruff) | Fast Python linter + formatter |
| **Type checking** | [pyright](https://github.com/microsoft/pyright) | Rust-based static analysis; first-class Pydantic v2 support |
| **Tests** | [pytest](https://pytest.org/) + hypothesis + soundfile | Unit, integration, and property-based tests |
| **CI** | GitHub Actions | ruff + pyright + pytest + alembic check + clippy on push |

---

## Project Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundation (uv, src-layout, config, Typer CLI) | ✅ Complete |
| 2 | Audio Analysis (librosa, 8 features, 262 tests) | ✅ Complete |
| 3 | Database & Auth (SQLModel, Alembic, JWT, RBAC) | ✅ Complete |
| 4 | CLI Modernization (21 commands, Rich, --json IPC) | ✅ Complete |
| 5 | Web UI (Flask, HTMX, SSE, waveform preview) | ✅ Complete |
| 6 | Desktop App (Tauri 2 + Svelte 5 Runes) | ✅ Complete |
| 7 | FL Studio Integration (filesystem, AppleScript, MIDI) | ✅ Complete |
| 8 | VST3/AU Plugin (JUCE 8, PythonSidecar IPC) | 🔄 90% — auval validation pending |
| 9 | Sample Packs (.smpack ZIP, SHA-256 integrity) | ✅ Complete |
| 10 | Production Release (signing, notarization, CI/CD) | 📋 Planned |
| 11 | Semantic Search (CLAP embeddings, sqlite-vec) | ✅ Complete |
| 12 | AI Curation (pydantic-ai, LiteLLM, smart playlists) | ✅ Complete |
| 13 | Cloud Sync (R2 file sync, Supabase metadata) | 🔄 90% — CRDT full merge pending |
| 14 | Analytics Dashboard (Plotly, BPM/key histograms) | ✅ Complete |
| 15 | Marketplace (Stripe checkout, R2 CDN, pack listings) | 🔄 70% — FastAPI routes pending |
| 16 | AI Generation (AudioCraft, Stable Audio, MockBackend) | 🔄 90% — GPU backends pending |

See [ROADMAP.md](ROADMAP.md) for the full roadmap.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the system architecture.
See [docs/en/](docs/en/) for detailed per-phase documentation.
See [docs/meta/](docs/meta/) for project meta and agent guides (agent routing, CLAUDE, and execution guides).

---

## Repository Structure

```
SampleMind-AI/
├── src/samplemind/          ← Python package (src-layout)
│   ├── cli/                 ← 21 Typer commands
│   ├── analyzer/            ← librosa audio analysis + classifiers
│   ├── data/                ← SQLModel + Alembic + repositories
│   ├── web/                 ← Flask HTMX web UI
│   ├── integrations/        ← FL Studio filesystem, AppleScript, MIDI
│   ├── packs/               ← .smpack builder/importer
│   ├── search/              ← CLAP embeddings + sqlite-vec index
│   ├── agent/               ← AI curation (pydantic-ai)
│   ├── sync/                ← R2 cloud sync + Supabase metadata
│   ├── analytics/           ← Plotly charts + summary engine
│   ├── marketplace/         ← Stripe + R2 pack listings
│   ├── generation/          ← Text-to-audio (AudioCraft, MockBackend)
│   └── sidecar/             ← Unix socket server for JUCE plugin
├── app/                     ← Tauri 2 desktop app
│   ├── src/                 ← Svelte 5 frontend
│   └── src-tauri/           ← Rust backend
├── plugin/                  ← JUCE 8 VST3/AU plugin
├── tests/                   ← pytest suite (262 tests, synthetic WAV fixtures)
├── docs/en/                 ← English phase documentation (phases 1–16)
├── docs/no/                 ← Norwegian phase documentation
├── scripts/                 ← Dev and release scripts
├── .claude/                 ← Claude Code agents and commands
└── .github/workflows/       ← CI/CD (ruff + pytest + clippy)
```

---

## Development Environment

This project is developed on **Windows WSL2 Ubuntu 24.04** and targets **macOS 12+ Universal Binary** for production.

> **Important:** Always develop on the Linux filesystem (`/home/ubuntu/...`), not `/mnt/c/` — the NTFS filesystem is 5–10× slower for Git and Python operations.

```bash
# Recommended WSL2 performance setup:
git config core.fsmonitor true
git config core.untrackedCache true
```

---

## Contributing

1. Fork the repo and create a feature branch
2. Run `./scripts/setup-dev.sh` to set up your dev environment
3. Make changes following the conventions in [CLAUDE.md](CLAUDE.md)
4. Run `uv run ruff check src/ && uv run pytest tests/ -n auto` before pushing
5. Open a pull request — CI will run automatically

**Key rules:**
- Use `uv` (not `pip`) for all Python dependency work
- Use `ruff` (not black/flake8) for linting and formatting
- Never commit real audio files — use synthetic fixtures in tests
- New CLI commands must output JSON to stdout when `--json` flag is passed

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for FL Studio producers who want to stop scrolling and start making.*
