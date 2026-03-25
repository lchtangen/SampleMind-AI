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

- **CLI** — `samplemind import`, `analyze`, `search`, `stats`, `duplicates`
- **Web UI** — Flask + HTMX browser interface with waveform preview
- **Desktop App** — Tauri 2 + Svelte 5 native app (macOS .dmg, Windows .msi)
- **VST3/AU Plugin** — Live sample browser inside FL Studio (JUCE 8, Phase 8)

Everything reads from the same SQLite database — no sync needed.

---

## Features

| Feature | Description |
|---------|-------------|
| **8-Feature Audio Analysis** | BPM, key, instrument, mood, energy, duration, spectral features |
| **AI Classification** | Automatic: kick/snare/hihat/bass/pad + dark/neutral/bright + low/medium/high |
| **Audio Fingerprinting** | SHA-256 dedup detection — find and remove exact duplicates |
| **Batch Import** | Parallel analysis with `--workers` (defaults to CPU count) |
| **SQLite Library** | WAL mode + FTS5 full-text search, < 50ms queries |
| **FL Studio Export** | Filesystem copy, clipboard path, AppleScript, MIDI metadata |
| **Sample Packs** | Export/import `.smpack` bundles with SHA-256 integrity |
| **Auto-Updater** | Sparkle (macOS) / NSIS (Windows) via GitHub Releases |
| **Offline-First** | Fully local — no cloud, no API keys required |

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
# Install all dependencies (creates .venv automatically):
uv sync

# Run the CLI:
uv run samplemind --help

# Import a folder of samples:
uv run samplemind import ~/Music/Samples/

# Search your library:
uv run samplemind search "dark kick"

# Show library statistics:
uv run samplemind stats

# Start the web UI (http://localhost:5000):
uv run samplemind serve
```

### Development Setup (WSL2)

```bash
# Run the dev setup script:
chmod +x scripts/setup-dev.sh && ./scripts/setup-dev.sh

# Run tests:
uv run pytest tests/ -v

# Run linter:
uv run ruff check src/

# Run full CI suite locally:
# (uses /check slash command in Claude Code)
uv run ruff check src/ && uv run pytest tests/ -n auto
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
| **ORM (target)** | SQLModel + Alembic | Type-safe DB with migration history |
| **CLI** | [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) | Beautiful terminal UX |
| **Web UI** | Flask + [HTMX](https://htmx.org/) | Browser interface, SSE progress |
| **Desktop app** | [Tauri 2](https://tauri.app/) | Native macOS/Windows app (~15 MB) |
| **Frontend** | [Svelte 5](https://svelte.dev/) Runes + Vite | Reactive desktop UI |
| **Plugin** | [JUCE 8](https://juce.com/) | VST3/AU plugin for FL Studio |
| **Lint/format** | [ruff](https://github.com/astral-sh/ruff) | Fast Python linter + formatter |
| **Tests** | [pytest](https://pytest.org/) + soundfile | Synthetic WAV fixtures |
| **CI** | GitHub Actions | pytest + ruff + clippy on push |

---

## Project Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundation (uv, src-layout, Typer CLI) | ✅ Complete |
| 2 | Audio Analysis & Testing | 🔄 In Progress |
| 3 | Database (SQLModel + Alembic + FTS5) | 📋 Planned |
| 4 | CLI Expansion (stats, duplicates, --workers) | 📋 Planned |
| 5 | Web UI (Flask-CORS, dark mode, bulk tag) | 📋 Planned |
| 6 | Desktop App (Tauri 2 + Svelte 5) | 📋 Planned |
| 7 | FL Studio Integration (AppleScript, MIDI) | 📋 Planned |
| 8 | VST3/AU Plugin (JUCE 8) | 📋 Planned |
| 9 | Sample Packs (.smpack format) | 📋 Planned |
| 10 | Production (signing, notarization, CI/CD) | 📋 Planned |

See [ROADMAP.md](ROADMAP.md) for the full roadmap.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the system architecture.
See [docs/en/](docs/en/) for detailed per-phase documentation.

---

## Repository Structure

```
SampleMind-AI/
├── src/samplemind/          ← Python package (src-layout)
│   ├── cli/                 ← Typer CLI commands
│   ├── analyzer/            ← librosa audio analysis
│   ├── data/                ← SQLite database layer
│   └── web/                 ← Flask web UI
├── app/                     ← Tauri 2 desktop app
│   ├── src/                 ← Svelte 5 frontend
│   └── src-tauri/           ← Rust backend
├── plugin/                  ← JUCE 8 VST3/AU plugin
├── tests/                   ← pytest suite (synthetic WAV fixtures)
├── docs/en/                 ← English phase documentation
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
