# AGENTS.md — Universal AI Agent Routing Guide

> **This file is the single source of truth for agent routing across all AI tools.**
> Read by: Augment Code (VS Code), Claude Code, GitHub Copilot, and any LLM-powered tool.
>
> Last updated: 2026-03-25

---

## AI Tool Directory Map

| Tool | Primary Config | Agents | Skills | Commands |
|------|---------------|--------|--------|----------|
| **Augment Code** (VS Code ext) | `.augment/rules.md` | `AGENTS.md` (this file) | `.augment/skills/*/SKILL.md` | VS Code tasks |
| **Claude Code** (claude.ai) | `CLAUDE.md` (root) | `.claude/agents/*.md` | `.claude/agents/*.md` | `.claude/commands/*.md` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | `.github/agents/*.md` | — | — |

> **`.auggie/`** = project YAML automation reference only. Not read by any AI extension.
> When adding new rules/skills, add to `.augment/` (Augment Code) and sync to other tools.

---

## Phase Agent Routing

Route tasks to the most specific phase agent first:

| Phase | Name | Key Technologies | Agent Files |
|-------|------|-----------------|-------------|
| 1 | Foundation | uv, structlog, pydantic-settings, health check | `phase-01-foundation` |
| 2 | Audio Analysis | librosa, LUFS, stereo, WAV fixtures, pytest | `phase-02-audio-testing` |
| 3 | Database | SQLModel, Alembic, FTS5, backup, multi-library | `phase-03-database` |
| 4 | CLI | Typer, Rich, watch mode, export, completion | `phase-04-cli` |
| 5 | Web UI | Flask, FastAPI, HTMX, Socket.IO, WaveSurfer | `phase-05-web` |
| 6 | Desktop | Tauri 2, Svelte 5 Runes, system tray | `phase-06-desktop` |
| 7 | FL Studio | AppleScript, MIDI clock, IAC Driver, COM | `phase-07-fl-studio` |
| 8 | JUCE Plugin | VST3/AU, sidecar IPC, presets, MIDI output | `phase-08-vst-plugin` |
| 9 | Sample Packs | .smpack format, registry, licensing | `phase-09-sample-packs` |
| 10 | Production | CI/CD, signing, feature flags, crash reporter | `phase-10-production` |
| 11 | Semantic Search | CLAP, FAISS, ChromaDB, text/audio similarity | `phase-11-semantic-search` |
| 12 | AI Curation | LiteLLM, Claude/Ollama, smart playlists | `phase-12-ai-curation` |
| 13 | Cloud Sync | Cloudflare R2, Supabase, multi-device | `phase-13-cloud-sync` |
| 14 | Analytics | Plotly, BPM histogram, key heatmap | `phase-14-analytics` |
| 15 | Marketplace | Stripe Connect, pack publishing, CDN | `phase-15-marketplace` |
| 16 | AI Generation | AudioCraft, Stable Audio, text-to-audio | `phase-16-ai-generation` |

---

## Cross-Cutting Domain Agent Routing

When the task spans multiple phases or involves a specific domain:

| If the task involves… | Use domain agent |
|-----------------------|-----------------|
| librosa, classifiers, WAV processing, fingerprinting, batch analysis | `audio-analyzer` |
| Tauri, Rust, Svelte 5, `app/` dir, IPC, build, macOS signing, GitHub Actions | `tauri-builder` |
| FL Studio, JUCE, VST3, AU, AppleScript, sidecar socket, `plugin/` dir | `fl-studio-agent` |
| `docs/en/`, `docs/no/`, phase docs, ARCHITECTURE.md, CLAUDE.md, README | `doc-writer` |
| pytest, cargo test, CI failures, test fixtures, coverage, conftest.py | `test-runner` |

---

## Routing Priority Rules

1. **Explicit phase reference** → use that phase's agent (e.g. "Phase 13" → `phase-13-cloud-sync`)
2. **Specific file path** → match the file to a phase (see phase table above)
3. **Keyword match** → use keyword list below
4. **Domain overlap** → use cross-cutting domain agent
5. **Not found** → use `audio-analyzer` as default for Python code, `tauri-builder` for Rust/Svelte

---

## Keyword → Agent Quick-Lookup

```
CLAP, FAISS, vector, embedding, semantic, cosine → phase-11-semantic-search
curate, LiteLLM, playlist, gap analysis, energy arc → phase-12-ai-curation
R2, S3, boto3, Supabase, sync push, sync pull → phase-13-cloud-sync
Plotly, analytics, histogram, heatmap, growth → phase-14-analytics
Stripe, marketplace, purchase, listing, CDN → phase-15-marketplace
AudioCraft, MusicGen, Stable Audio, generate → phase-16-ai-generation
librosa, analyze, BPM, key, instrument, LUFS → audio-analyzer OR phase-02
SQLModel, Alembic, migration, repository → phase-03-database
Typer, Rich, CLI, watch, export → phase-04-cli
Flask, FastAPI, HTMX, Socket.IO, WaveSurfer → phase-05-web
Tauri, Rust, Svelte, invoke, cargo → tauri-builder OR phase-06
FL Studio, AppleScript, IAC Driver, MIDI clock → fl-studio-agent OR phase-07
JUCE, VST3, AU, auval, PluginProcessor → fl-studio-agent OR phase-08
.smpack, manifest.json, pack registry → phase-09-sample-packs
CI, GitHub Actions, signing, notarization → phase-10-production
pytest, conftest, WAV fixture, coverage → test-runner OR phase-02
docs/, ARCHITECTURE.md, README → doc-writer
```

---

## Critical Project Rules (apply always)

### Never do
- `pip install` — use `uv add`
- `npm` in `app/` — use `pnpm`
- `black`, `flake8`, `pylint`, `isort` — use `ruff` only
- commit real WAV/AIFF/MP3 files — use synthetic fixtures
- hardcode home directory paths — use `platformdirs`
- print JSON to stderr or human text to stdout — breaks Tauri IPC
- use `sys.path.insert` in new code
- add `clippy` suppressions without a comment
- commit `.env` files or credentials

### Always do
- Type annotations on all new public functions
- `cargo clippy -- -D warnings` must pass before commit
- New Tauri commands: register in `invoke_handler!` AND `capabilities/*.json`
- New CLI commands: `--json` flag outputs JSON to stdout
- New audio features: need pytest fixture + test + `@pytest.mark.slow` if > 1s

### Classifier output values (never deviate)

| Field | Valid values |
|-------|-------------|
| `energy` | `"low"` `"mid"` `"high"` — ⚠ **never `"medium"`** |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` |

---

## Quick Command Reference

```bash
# Python
uv sync && uv run samplemind --help
uv run pytest tests/ -v -m "not slow"
uv run ruff check src/ && uv run ruff format src/

# Tauri
cd app && pnpm install && pnpm tauri dev

# Rust
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings

# Phase 11–16
uv run samplemind semantic "query" --top 20
uv run samplemind curate analyze
uv run samplemind sync push
uv run samplemind analytics --json
uv run samplemind generate "dark kick" --bpm 140 --model mock
uv run samplemind index rebuild
```
