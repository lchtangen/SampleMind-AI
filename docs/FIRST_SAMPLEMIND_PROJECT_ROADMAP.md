# SampleMind AI — Master Roadmap (2026–2030)

> **The authoritative engineering and product vision document.**
> Covers architecture, all development phases, AI/ML strategy, and the 2026–2030 product trajectory.
> Version: 3.0 | Updated: 2026-03-25 | Status: Active Development — v0.2.0

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [System Architecture](#2-system-architecture)
3. [Tech Stack — Current & Target (2026–2030)](#3-tech-stack--current--target-20262030)
4. [Phase Status (March 2026)](#4-phase-status-march-2026)
5. [13-Phase Development Plan](#5-13-phase-development-plan)
6. [AI & ML Strategy](#6-ai--ml-strategy)
7. [Sprint Planning](#7-sprint-planning)
8. [Long-Term Vision (2027–2030)](#8-long-term-vision-20272030)
9. [Performance Targets & SLAs](#9-performance-targets--slas)
10. [Testing & Quality](#10-testing--quality)
11. [Technical Debt](#11-technical-debt)
12. [Risk Management](#12-risk-management)
13. [Contribution Guide](#13-contribution-guide)

---

## 1. Project Vision

**SampleMind AI** is a **local-first, AI-powered audio sample library manager and
DAW companion** for music producers. It combines traditional signal-processing analysis
(librosa), neural audio embeddings (CLAP), vector similarity search (sqlite-vec), and
AI agent automation (pydantic-ai + Ollama) — all running **offline on your own machine**.

Everything — CLI, Flask web UI, Tauri desktop app, JUCE VST3/AU plugin — reads the
same SQLite database, enhanced with vector embeddings for semantic search.

### Core Pillars

**Analyze** — Extract BPM, key, instrument, mood, energy, and 8 acoustic features from
every sample using librosa 0.11 + rule-based classifiers. Future: CLAP neural embeddings
for zero-shot zero-label classification.

**Organize** — Store rich metadata in SQLite (SQLModel + Alembic) with full-text FTS5
search, tag filtering, fingerprint deduplication, and **512-dim vector embeddings** stored
in sqlite-vec for sub-millisecond semantic retrieval.

**Search Semantically** — Type *"punchy 808 with sub tail"* or *"dark atmospheric pad in A minor"*
and get ranked results via cosine similarity on CLAP audio embeddings. No keywords required.

**Automate with Agents** — pydantic-ai agents (powered by Claude, GPT-4o, or local Ollama)
auto-tag libraries, answer natural-language questions about your samples, and suggest sounds
for active projects — all with type-safe tool calls and structured JSON responses.

**Integrate** — Connect with FL Studio via filesystem export, clipboard, AppleScript
automation, virtual MIDI, and a native JUCE VST3/AU plugin.

**Ship** — Distribute as a signed, notarized macOS Universal Binary (arm64 + x86_64)
with a PyInstaller-bundled Python sidecar, auto-updater, and `.smpack` sample pack format.

### What This Is NOT

- No mandatory cloud sync or SaaS subscription — everything runs fully offline
- AI agents default to local Ollama (no API key) — cloud APIs are opt-in
- No Electron, no React, no MongoDB — see [Tech Stack](#3-tech-stack--current--target-20262030)
- Not a DAW — a companion tool that lives alongside FL Studio (and other DAWs)

---

## 2. System Architecture

### Five-Layer Architecture (2026 Target)

```text
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5 — DAW Integration                                      │
│  ┌─────────────────────┐   ┌──────────────────────────────────┐ │
│  │  JUCE Plugin (C++)  │   │  FL Studio / Any DAW             │ │
│  │  VST3 + AU          │   │  - Filesystem browser            │ │
│  │  PluginEditor UI    │   │  - AppleScript automation        │ │
│  │  PythonSidecar      │   │  - Virtual MIDI (IAC Driver)     │ │
│  └──────────┬──────────┘   └──────────────────────────────────┘ │
└─────────────┼───────────────────────────────────────────────────┘
              │ Unix domain socket (~/tmp/samplemind.sock)
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 4 — Desktop Application (Tauri 2 + Svelte 5)             │
│  ┌──────────┴──────────┐                                        │
│  │  Svelte 5 Runes     │  SampleTable, SemanticSearch,          │
│  │  (WKWebView macOS)  │  WaveformPlayer, AgentChat             │
│  └──────────┬──────────┘                                        │
│             │ tauri::invoke() IPC                               │
│  ┌──────────┴──────────┐                                        │
│  │  Rust (Tauri core)  │  import_folder, search_semantic,       │
│  │  app/src-tauri/     │  pick_folder_dialog, agent_ask         │
│  └──────────┬──────────┘                                        │
└─────────────┼───────────────────────────────────────────────────┘
              │ stdout JSON  (samplemind import --json ...)
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 3 — Python Backend                                       │
│  ┌──────────┴──────────┐                                        │
│  │  Typer CLI + FastAPI │  import, analyze, search, tag,        │
│  │  src/samplemind/     │  serve, agent, export, pack           │
│  └──────────┬──────────┘                                        │
│  ┌──────────┴──────────────────────────────────────────────┐    │
│  │  Core Services                                           │    │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │    │
│  │  │  Audio Analysis  │  │  Sample Repository            │ │    │
│  │  │  librosa 0.11    │  │  SQLModel + Alembic           │ │    │
│  │  │  8 rule features │  │  SampleRepository             │ │    │
│  │  └──────────────────┘  └──────────────────────────────┘ │    │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │    │
│  │  │  Embeddings      │  │  AI Agent Layer               │ │    │
│  │  │  CLAP encoder    │  │  pydantic-ai + tools          │ │    │
│  │  │  sqlite-vec ANN  │  │  Ollama / Claude / GPT        │ │    │
│  │  └──────────────────┘  └──────────────────────────────┘ │    │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │    │
│  │  │  Flask Web UI    │  │  Pack System                  │ │    │
│  │  │  HTMX + SSE      │  │  .smpack ZIP format           │ │    │
│  │  └──────────────────┘  └──────────────────────────────┘ │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 2 — AI / Embedding Services (optional, local)            │
│  ┌──────────┴──────────┐   ┌──────────────────────────────────┐ │
│  │  Ollama             │   │  HuggingFace ClapModel            │ │
│  │  llama3.3 (offline) │   │  CLAP music/audio embeddings      │ │
│  │  qwen2.5-coder      │   │  sentence-transformers (text)     │ │
│  │  gemma3             │   │  (loaded on-demand, no server)    │ │
│  └─────────────────────┘   └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 1 — Storage                                              │
│  ┌──────────┴──────────┐   ┌──────────────────────────────────┐ │
│  │  SQLite DB          │   │  Audio Files                     │ │
│  │  + sqlite-vec       │   │  ~/Music/SampleMind/             │ │
│  │  (WAL, FTS5,        │   │  (WAV/AIFF, paths preserved)     │ │
│  │   vector ANN idx)   │   │                                  │ │
│  └─────────────────────┘   └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### IPC Contract

All Rust (Tauri) ↔ Python communication uses **stdout JSON** exclusively.
Python logs status/progress to **stderr only** — never stdout. This is a hard contract.

| Tauri Command | Python CLI Invocation | JSON Response |
| --- | --- | --- |
| `import_folder` | `samplemind import <path> --json` | `{"imported": N, "errors": M, "samples": [...]}` |
| `search_samples` | `samplemind search --query X --json` | `{"samples": [...]}` |
| `search_semantic` | `samplemind search "dark kick" --semantic --json` | `{"samples": [...], "query_ms": N}` |
| `analyze_file` | `samplemind analyze <path> --json` | `{"bpm": F, "key": S, "energy": S, ...}` |
| `get_library_stats` | `samplemind list --stats --json` | `{"total": N, "by_instrument": {...}}` |
| `agent_ask` | `samplemind agent ask "..." --json` | `{"answer": S, "samples": [...]}` |
| `export_pack` | `samplemind pack create NAME SLUG --json` | `{"pack_path": S, "sample_count": N}` |

### Python Sidecar Socket Protocol (JUCE Plugin)

Length-prefixed JSON over Unix domain socket (`~/tmp/samplemind.sock`):

```text
Request:  [4-byte big-endian length] [UTF-8 JSON]
Response: [4-byte big-endian length] [UTF-8 JSON]

{"version": 2, "action": "ping"}
{"version": 2, "action": "search", "query": "...", "energy": "high"}
{"version": 2, "action": "analyze", "path": "/abs/path/file.wav"}
```

---

## 3. Tech Stack — Current & Target (2026–2030)

### Migration State

| Component | Current (v0.2.0) | Target (v1.0) | Phase |
| --- | --- | --- | --- |
| Package manager | uv ≥0.6 + pyproject.toml | ✅ live | — |
| Python version | 3.13 (JIT preview) | 3.14 free-threaded (2028) | — |
| Package layout | src/samplemind/ | ✅ live | — |
| Auth | JWT + RBAC (FastAPI) | ✅ live | 3 |
| Database | SQLModel + Alembic | ✅ live | 4 |
| Vector search | sqlite-vec (installed) | ANN index + CLAP embeddings | 12 |
| AI agents | pydantic-ai (installed) | Agent CLI + Tauri chat | 13 |
| CLI | Typer + Rich + `--json` | + `agent` + `search --semantic` | 5 |
| Web UI | Flask + Jinja2 | Flask + HTMX + SSE + semantic search | 6 |
| Desktop frontend | Tauri shell + Flask WebView | Svelte 5 Runes + pnpm | 7 |
| FL Studio | none | filesystem + AppleScript + MIDI | 8 |
| Plugin | none | JUCE 8 VST3/AU | 9 |
| Sample packs | none | .smpack ZIP + SHA-256 manifest | 10 |
| Distribution | none | PyInstaller sidecar + notarized DMG/MSI | 11 |
| Lint / format | ruff ≥0.15 | ✅ live | — |
| Type checking | pyright ≥1.1.390 | ✅ live | — |
| Tests | pytest ≥9 + hypothesis | ✅ live | — |
| Observability | structlog → stderr | Logfire (OpenTelemetry) | 11 |
| CI | uv + ruff + pytest + clippy | + pyright + alembic check | — |

### Full Technology Decision Log

| Technology | Replaces | Rationale | Status |
| --- | --- | --- | --- |
| **uv** (Astral) | pip + venv | 10–100× faster; workspace support; `uv run` replaces scripts | ✅ |
| **pyproject.toml** | requirements.txt | PEP 621; deps + scripts + tool config in one file | ✅ |
| **src-layout** | flat layout | Prevents accidental import of source tree | ✅ |
| **SQLModel** | raw sqlite3 | Type-safe ORM: SQLAlchemy 2.0 + Pydantic v2 in one class | ✅ |
| **Alembic** | `_migrate()` hack | Versioned, reversible migrations; `alembic check` in CI | ✅ |
| **bcrypt (direct)** | passlib[bcrypt] | passlib 1.7.x fails to parse bcrypt 4.x/5.x version strings | ✅ |
| **FastAPI** | Flask (for API) | Async; auto OpenAPI docs; Pydantic v2 native integration | ✅ |
| **StaticPool** in tests | thread-local pools | In-memory SQLite shared across threads (FastAPI test fix) | ✅ |
| **sqlite-vec** | Qdrant / pgvector | C extension; zero extra infra; ANN inside existing SQLite DB | ✅ |
| **pydantic-ai** | LangChain | Type-safe; model-agnostic; structured outputs; smaller API | ✅ |
| **hypothesis** | manual edge cases | Property-based fuzzing; finds edge cases no human writes | ✅ |
| **pyright** | mypy | Rust-based; 10–100× faster; first-class Pydantic v2 support | ✅ |
| **Typer + Rich** | argparse | Type annotations → auto `--help`; Rich tables + progress | ✅ |
| **HTMX** | custom JS fetch | 80% less JS with HTML attributes; pairs with Flask SSE | 📋 Phase 6 |
| **Svelte 5 Runes** | Svelte 4 / React | Fine-grained reactivity; `.svelte.ts` stores; 0 virtual DOM | 📋 Phase 7 |
| **Tauri 2** | Electron | 3–15 MB vs 120–200 MB; Rust; WKWebView; capability security | 📋 Phase 7 |
| **CLAP (HuggingFace)** | laion-clap | numpy 2.x compatible; zero-shot audio↔text classification | 📋 Phase 12 |
| **Ollama** | OpenAI API | Fully offline; llama3.3, qwen2.5, gemma3; pydantic-ai native | 📋 Phase 13 |
| **Logfire** (Pydantic) | print + structlog | OpenTelemetry-native; auto-instruments FastAPI + SQLModel | 📋 Phase 11 |
| **JUCE 8** | — | VST3 + AU from one C++ codebase; PluginEditor + sidecar | 📋 Phase 9 |
| **PyInstaller** | requiring Python | Standalone sidecar binary for end-user distribution | 📋 Phase 11 |
| **Python 3.14 no-GIL** | GIL-limited threads | PEP 703: true parallel audio workers (2028 migration) | 🔮 2028 |

### Audio Analysis Pipeline (Current + Future)

```text
WAV file
  │
  ├─ [Current: librosa 0.11]
  │    └─ librosa.load(sr=22050, mono=True)
  │         ├─ BPM:   beat_track() → tempo in BPM
  │         ├─ Key:   chroma_cens() + tonnetz() → root + major/minor
  │         └─ 8 features → 3 rule-based classifiers:
  │              rms, spectral_centroid, zero_crossing_rate
  │              spectral_flatness, spectral_rolloff
  │              onset_mean/max, low_freq_ratio, duration
  │              → classify_energy()     → "low" | "mid" | "high"
  │              → classify_mood()       → "dark" | "chill" | "aggressive" | "euphoric"
  │              → classify_instrument() → "kick" | "snare" | "hihat" | "bass" | ...
  │
  └─ [Phase 12: CLAP neural embeddings]
       └─ ClapModel.from_pretrained("laion/larger_clap_music")
            └─ 512-dim float32 audio embedding
                 └─ sqlite-vec: INSERT INTO ann_samples(embedding) VALUES (?)
                      └─ Query: "dark atmospheric pad" → text embedding →
                           → cosine ANN search → top-K sample IDs → JOIN samples
```

---

## 4. Phase Status (March 2026)

```text
Phase 1  — Foundation & CLI      ████████████████████  100% ✅
Phase 2  — Audio Analysis        ████████████████████  100% ✅
Phase 3  — Authentication        ████████████████████  100% ✅
Phase 4  — Database (SQLModel)   ████████████████████  100% ✅
Phase 5  — CLI Modernization     ░░░░░░░░░░░░░░░░░░░░    0% 📋
Phase 6  — Web UI (HTMX)         ░░░░░░░░░░░░░░░░░░░░    0% 📋
Phase 7  — Tauri + Svelte 5      ████░░░░░░░░░░░░░░░░   20% 🔄 (foundation only)
Phase 8  — FL Studio             ░░░░░░░░░░░░░░░░░░░░    0% 📋
Phase 9  — JUCE Plugin           ░░░░░░░░░░░░░░░░░░░░    0% 📋
Phase 10 — Sample Packs          ░░░░░░░░░░░░░░░░░░░░    0% 📋
Phase 11 — Production            ░░░░░░░░░░░░░░░░░░░░    0% 📋
Phase 12 — Semantic Search       ████░░░░░░░░░░░░░░░░   10% 🔄 (sqlite-vec installed)
Phase 13 — AI Agent Automation   ████░░░░░░░░░░░░░░░░   10% 🔄 (pydantic-ai installed)

Overall: ~48% complete (core infrastructure solid; AI + desktop phases ahead)
```

| Phase | Deliverable | Key Tech |
| --- | --- | --- |
| ✅ 1 | Foundation, CLI, src-layout | uv, Typer, pyproject.toml |
| ✅ 2 | Audio analysis, 33 tests | librosa 0.11, pytest, soundfile fixtures |
| ✅ 3 | JWT auth, RBAC, user model | FastAPI, bcrypt, python-jose, SQLModel |
| ✅ 4 | Sample model, SampleRepository, WAL mode | SQLModel, Alembic, sqlite-vec (installed) |
| 📋 5 | stats/duplicates CLI, --workers | Typer, ProcessPoolExecutor |
| 📋 6 | HTMX search, SSE import progress | HTMX, Flask SSE, wavesurfer.js |
| 🔄 7 | Svelte 5 Runes desktop | Tauri 2, Svelte 5, pnpm |
| 📋 8 | FL Studio filesystem + MIDI | AppleScript, python-rtmidi |
| 📋 9 | VST3/AU plugin | JUCE 8, C++, Unix socket |
| 📋 10 | .smpack packs | ZIP, SHA-256 |
| 📋 11 | Signed DMG/MSI, Logfire | PyInstaller, GitHub Actions |
| 🔄 12 | Semantic search | sqlite-vec ANN, CLAP embeddings |
| 🔄 13 | AI agent CLI + API | pydantic-ai, Ollama |

---

## 5. 13-Phase Development Plan

---

### Phase 1 — Foundation ✅

**Goal:** Establish a modern Python 3.13 project with uv, src-layout, CI, and dev tooling.

**Deliverables:**

- `pyproject.toml` with all deps, ruff, pytest, coverage configuration
- `src/samplemind/` package with `__init__.py`, `__main__.py`, cli/, analyzer/, data/, web/
- `.python-version` pinned to 3.13
- `.github/workflows/python-lint.yml` — uv + ruff + pytest + Rust clippy
- `scripts/setup-dev.sh` bootstrap for new contributors
- `.vscode/settings.json` for WSL2 development
- `.pre-commit-config.yaml` with ruff hooks
- `.editorconfig` for consistent indentation

**Success criteria:**

- `uv sync && uv run pytest` passes from a clean clone
- `uv run ruff check src/` reports zero errors
- `cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings` passes

**Phase doc:** [docs/en/phase-01-foundation.md](en/phase-01-foundation.md)

---

### Phase 2 — Audio Analysis & AI Classification 🔄

**Goal:** Fully test and extend the librosa-based analysis pipeline with batch processing,
fingerprinting, and comprehensive test coverage.

**Deliverables:**

- All 8 features tested in `tests/test_audio_analysis.py`
- All 3 classifiers tested in `tests/test_classifier.py` with 90%+ coverage
- `kick_wav`, `hihat_wav`, `bass_wav`, `silent_wav` fixtures in `tests/conftest.py`
- Batch analysis with `ProcessPoolExecutor` and `--workers N` flag
- Audio fingerprinting: SHA-256 of first 64 KB for deduplication
- Analysis cache: skip re-analysis if file `mtime` is unchanged
- `samplemind duplicates [--remove]` CLI command

**Key tech decisions:**

- Always load at `sr=22050, mono=True` for deterministic results
- `ProcessPoolExecutor` (not ThreadPoolExecutor) — CPU-bound work
- SHA-256 fingerprint of raw bytes (not acoustic hash) — fast and collision-resistant

**Success criteria:**

- `uv run pytest tests/ --cov=samplemind --cov-report=term-missing` → analyzer 80%+
- Batch import of 100 synthetic WAVs completes in < 30s on 8-core machine
- `samplemind duplicates` finds injected duplicates with zero false positives

**Phase doc:** [docs/en/phase-02-audio-analysis.md](en/phase-02-audio-analysis.md)

---

### Phase 3 — Database & Data Layer 📋

**Goal:** Migrate from raw sqlite3 to SQLModel + Alembic with the Repository pattern,
FTS5 full-text search, and WAL mode.

**Deliverables:**

- `alembic/` directory initialized with `alembic.ini` and `versions/`
- `alembic/versions/0001_initial.py` — initial schema migration
- `src/samplemind/models.py` — `Sample` SQLModel class
- `src/samplemind/data/repository.py` — `SampleRepository` with typed methods:
  `upsert()`, `tag()`, `search()`, `get_by_name()`, `count()`, `get_all()`
- `src/samplemind/data/db.py` — engine setup with platformdirs path and PRAGMA settings
- `tests/test_repository.py` with in-memory SQLite session fixture
- FTS5 virtual table for search (< 50ms on 10k samples)
- WAL mode enabled by default

**Key tech decisions:**

- SQLModel = SQLAlchemy 2.0 + Pydantic — one model for both ORM and validation
- Alembic replaces the `_migrate()` function — proper version history in CI
- In-memory SQLite (`sqlite://`) for all tests — never write to disk in pytest

**PRAGMA settings** (applied on engine creation):

```sql
PRAGMA journal_mode=WAL;
PRAGMA cache_size = -64000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
```

**Success criteria:**

- `alembic upgrade head` runs cleanly from a fresh clone
- `SampleRepository.search(query="kick", energy="high")` returns in < 50ms on 10k rows
- All existing sqlite3 tests pass with no behavior changes

**Phase doc:** [docs/en/phase-03-database.md](en/phase-03-database.md)

---

### Phase 4 — CLI with Typer and Rich 🔄

**Goal:** Complete the Typer CLI with all 8 commands, `--json` IPC mode, Rich progress
bars, and shell completion.

**Deliverables:**

- All 6 existing commands (`import`, `analyze`, `list`, `search`, `tag`, `serve`)
  with `--json` flag outputting machine-readable JSON to stdout ✅
- `samplemind stats [--json]` — library statistics
- `samplemind duplicates [--remove]` — find/remove duplicates by fingerprint
- Rich progress bar during import with ETA and per-file status
- Shell completion: `samplemind --install-completion`
- `tests/test_cli.py` with Typer `CliRunner` and 70%+ coverage

**IPC contract (non-negotiable):**

- JSON to stdout only — Rust reads this
- Human-readable text to stderr only — never mix
- `--json` flag on all data-returning commands

**Success criteria:**

- `samplemind import /path/to/samples --json | python -m json.tool` validates cleanly
- `samplemind stats --json` returns `{"total": N, "by_instrument": {...}}`
- Shell completion works in bash and zsh

**Phase doc:** [docs/en/phase-04-cli.md](en/phase-04-cli.md)

---

### Phase 5 — Web UI with Flask and HTMX 🔄

**Goal:** Upgrade Flask to a factory pattern with Blueprints, HTMX live search, and
SSE import progress.

**Deliverables:**

- `create_app()` factory with test configuration
- Blueprint structure: `library` (search/list/tag) and `import_` (upload + SSE)
- HTMX live search with 300ms debounce — no page reload
- SSE stream for import progress: `start → progress (N/total) → done`
- Waveform preview with Wavesurfer.js
- `POST /api/samples/bulk-tag` — bulk tag by ID list
- `GET /api/samples/stats` — library statistics endpoint
- `flask-cors` configured for `tauri://localhost` origin
- `tests/test_web.py` with Flask test client and in-memory database

**Key tech decisions:**

- HTMX replaces 80% of JavaScript — HTML attributes drive server interactions
- SSE (not WebSocket) for progress — simpler, unidirectional, no handshake
- Keep API response shapes stable — Tauri and app.js consume them

**Success criteria:**

- Import of 50 files streams progress to browser without polling
- Live search responds within 300ms on 10k-sample library
- All API endpoints return correct JSON with `flask-cors` headers

**Phase doc:** [docs/en/phase-05-web-ui.md](en/phase-05-web-ui.md)

---

### Phase 6 — Desktop App with Tauri 2 and Svelte 5 🔄

**Goal:** Build the complete Svelte 5 frontend with Runes-based reactivity backed by
Tauri 2 Rust commands that spawn the Python CLI.

**Deliverables:**

- `app/src/` scaffolded with Svelte 5 + Vite + TypeScript
- `app/vite.config.ts` targeting Tauri dev server
- Library store: `app/src/lib/stores/library.svelte.ts` with `$state` Runes
- Components: `SampleTable.svelte`, `ImportPanel.svelte`, `WaveformPlayer.svelte`
- Typed invoke wrappers: `app/src/lib/api/tauri.ts`
- Rust commands: `import_folder`, `search_samples`, `pick_folder_dialog`
- System tray: show/hide window, quit
- HMR (Hot Module Replacement) in `pnpm tauri dev`
- `app/src-tauri/capabilities/default.json` with all command permissions

**Svelte 5 Runes pattern:**

```svelte
<script lang="ts">
  let query = $state('');
  let results = $derived.by(async () => await searchSamples(query));
</script>
```

**Success criteria:**

- `pnpm tauri dev` starts with HMR, no console errors
- Import folder dialog opens and drives progress visible in ImportPanel
- SampleTable updates reactively as search query changes
- `pnpm tauri build` produces a distributable bundle

**Phase doc:** [docs/en/phase-06-desktop-app.md](en/phase-06-desktop-app.md)

---

### Phase 7 — FL Studio Integration 📋

**Goal:** Connect SampleMind to FL Studio at all 4 integration levels: filesystem,
clipboard, AppleScript automation, and virtual MIDI.

**Deliverables:**

- `src/samplemind/integrations/paths.py` — FL Studio 20/21 path detection (macOS + Windows)
- `src/samplemind/integrations/filesystem.py` — `export_to_fl_studio()` with folder
  organization by instrument/mood/genre
- `src/samplemind/integrations/clipboard.py` — `copy_sample_path()` (pbcopy / clip.exe)
- `src/samplemind/integrations/applescript.py` — `focus_fl_studio()`,
  `is_fl_studio_running()`, `open_sample_browser()`
- `src/samplemind/integrations/midi.py` — virtual MIDI port via python-rtmidi,
  CC messages for BPM/key metadata
- `src/samplemind/integrations/naming.py` — `kick_128bpm_Cmin.wav` naming scheme
- `entitlements.plist` with `com.apple.security.automation.apple-events` ✅
- Tauri command: `focus_fl_studio` → osascript call

**FL Studio macOS paths:**

```text
~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/    ← FL20
~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/ ← FL21
```

**Success criteria:**

- `samplemind export --fl-studio` copies samples to correct FL Studio folder
- `focus_fl_studio()` brings FL Studio to front without permission error
- Virtual MIDI port appears in FL Studio MIDI settings

**Phase doc:** [docs/en/phase-07-fl-studio.md](en/phase-07-fl-studio.md)

---

### Phase 8 — VST3/AU Plugin with JUCE 8 📋

**Goal:** Build a JUCE 8 C++ plugin that runs inside FL Studio and communicates with
the Python sidecar via Unix domain socket.

**Deliverables:**

- `plugin/CMakeLists.txt` with JUCE 8 VST3 + AU targets
- `plugin/src/PluginProcessor.h/.cpp` — audio passthrough, state management
- `plugin/src/PluginEditor.h/.cpp` — UI with search field, sample list, waveform
- `plugin/src/PythonSidecar.h/.cpp` — launch, communicate, stop lifecycle
- `plugin/src/IPCSocket.h/.cpp` — length-prefixed JSON over Unix domain socket
- `src/samplemind/sidecar/server.py` — asyncio socket server (search, analyze, ping)
- Sidecar health-check ping every 5s; auto-restart on timeout (max 3 retries)
- `auval -v aufx SmPl SmAI` passes on macOS

**Sidecar startup sequence:**

1. `PluginProcessor::prepareToPlay()` → `sidecar.launch(binaryPath)`
2. Wait for `{"status": "ready", "version": 2}` on stdout
3. Begin 5s ping loop
4. On editor close: `sidecar.shutdown()`

**Success criteria:**

- Plugin loads in FL Studio without crash
- Search in plugin UI returns results from local SQLite library
- `auval -v aufx SmPl SmAI` exits 0 on macOS

**Phase doc:** [docs/en/phase-08-vst-plugin.md](en/phase-08-vst-plugin.md)

---

### Phase 9 — Sample Packs (.smpack) 📋

**Goal:** Build a portable `.smpack` format (ZIP + JSON manifest) for exporting, sharing,
and importing curated sample libraries with SHA-256 integrity verification.

**Deliverables:**

- `.smpack` format: `manifest.json` + `samples/` inside a ZIP archive
- `src/samplemind/packs/manifest.py` — `PackManifest` Pydantic model with `SampleEntry`
- `src/samplemind/packs/exporter.py` — `export_pack()` filtering library into ZIP
- `src/samplemind/packs/importer.py` — `import_pack()` with SHA-256 verification,
  idempotent upsert
- CLI commands: `pack create NAME SLUG`, `pack import FILE`, `pack verify FILE`,
  `pack list`
- `scripts/release-pack.sh` — create GitHub Release with `.smpack` as asset
- `tests/test_packs.py` — roundtrip export → import test

**Manifest schema:**

```json
{
  "name": "Dark Trap Kit Vol.1",
  "slug": "dark-trap-kit-v1",
  "version": "1.0.0",
  "format_version": 1,
  "author": "lchtangen",
  "samples": [
    {"file": "samples/kick.wav", "sha256": "abc123...", "bpm": 128.0, "key": "C min"}
  ]
}
```

**Success criteria:**

- Export + import roundtrip preserves all metadata with zero data loss
- SHA-256 mismatch causes import to abort with clear error
- `pack verify` passes on a valid pack, fails on a corrupted one

**Phase doc:** [docs/en/phase-09-sample-packs.md](en/phase-09-sample-packs.md)

---

### Phase 10 — Production & Distribution 📋

**Goal:** Sign, notarize, and distribute SampleMind as a native macOS Universal Binary
and Windows installer via automated GitHub Actions.

**Deliverables:**

- `scripts/bump-version.sh` — sync version across `pyproject.toml`, `Cargo.toml`,
  `tauri.conf.json`, `package.json`
- `scripts/build-sidecar.sh` — PyInstaller one-file bundle from `samplemind-server.spec`
- `scripts/release-pack.sh` — GitHub Release creation ✅ (Phase 9)
- `.github/workflows/release.yml` — macOS Universal Binary build + signing +
  notarization + Windows MSI build
- `app/src-tauri/entitlements.plist` — all required Apple entitlements ✅
- Tauri auto-updater with GitHub Releases endpoint
- Sentry crash reporting wired to `SAMPLEMIND_SENTRY_DSN` env var (opt-in)
- Production release checklist in `docs/en/phase-10-production.md`

**macOS entitlements required:**

- `com.apple.security.automation.apple-events` (AppleScript)
- `com.apple.security.cs.allow-unsigned-executable-memory` (Python sidecar)
- `com.apple.security.files.user-selected.read-write` (file access)
- `com.apple.security.assets.music.read-write` (Music folder)

**Success criteria:**

- `pnpm tauri build --target universal-apple-darwin` produces a notarized `.dmg`
- `xcrun stapler validate SampleMind.app` exits 0
- Auto-updater detects and installs a staged update from GitHub Releases
- Sentry receives a test event when `SAMPLEMIND_SENTRY_DSN` is set

**Phase doc:** [docs/en/phase-10-production.md](en/phase-10-production.md)

---

## 6. AI & ML Strategy

### Guiding Principles

1. **Local-first by default** — All AI features work offline. Cloud APIs are opt-in.
2. **Progressive enhancement** — Phases 1–11 work without any AI models installed.
   Phases 12–13 enhance the experience when models are available.
3. **No numpy version hell** — All AI packages must support numpy ≥2.0.
   Legacy packages requiring numpy <2.0 (laion-clap, madmom) require a separate conda environment.
4. **Structured outputs only** — pydantic-ai agents always return typed Pydantic models.
   No free-form string parsing. JSON to stdout, logs to stderr.
5. **Deterministic fallback** — If an AI model is unavailable, the system falls back
   to the rule-based classifier (Phase 2). No silent failures.

### AI Component Map

| Component | Technology | Model | Input | Output | Phase |
| --- | --- | --- | --- | --- | --- |
| Rule-based classifier | librosa + sklearn | N/A | audio features | energy/mood/instrument | ✅ 2 |
| Audio embeddings | HuggingFace ClapModel | laion/larger_clap_music | WAV file | 512-dim float32 | 📋 12 |
| Text embeddings | sentence-transformers | all-MiniLM-L6-v2 | tag text | 384-dim float32 | 📋 12 |
| Vector ANN search | sqlite-vec | N/A | query embedding | sample IDs + distances | 📋 12 |
| Library agent | pydantic-ai + Ollama | llama3.3 (offline) | natural language | structured results | 📋 13 |
| Cloud agent | pydantic-ai + Anthropic | claude-3-5-sonnet | natural language | structured results | 📋 13 |

### Phase 12 — Semantic Search Implementation

```python
# Embedding pipeline (runs at import time, stored in sqlite-vec)
encode_audio(path) → ClapModel → 512-dim float32 → struct.pack("512f") → BLOB
encode_text(query) → ClapProcessor → 512-dim float32 → BLOB

# ANN query
"dark atmospheric pad" → encode_text() → cosine_similarity(ann_samples) → top-10 sample IDs
```

**sqlite-vec table:**
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS ann_samples USING vec0(
    embedding float[512]   -- CLAP audio embedding, L2-normalized
);
```

**Performance target:** < 50ms for KNN search over 100K samples on MacBook Air M3.

### Phase 13 — AI Agent Tools

pydantic-ai auto-discovers tools from Python type annotations:

```python
@agent.tool
def search_samples(ctx: RunContext, query: str, energy: str | None = None) -> list[SampleResult]:
    """Search the sample library. Use this for any 'find me samples' request."""
    ...

@agent.tool
def get_library_stats(ctx: RunContext) -> LibraryStats:
    """Get count, breakdown by instrument, mood, energy. Use to answer 'how many' questions."""
    ...

@agent.tool
def semantic_search(ctx: RunContext, description: str, k: int = 10) -> list[SampleResult]:
    """Find samples by natural language description using vector similarity."""
    ...
```

### Supported Model Providers (pydantic-ai)

| Provider | Model | Offline? | Notes |
| --- | --- | --- | --- |
| Ollama | llama3.3 (70B) | ✅ Yes | Best offline reasoning; 48GB+ RAM |
| Ollama | qwen2.5-coder:7b | ✅ Yes | Fast tool use; 8GB RAM |
| Ollama | gemma3:12b | ✅ Yes | Google model; good for structured output |
| Anthropic | claude-3-5-sonnet-latest | ❌ API key | Best overall quality |
| OpenAI | gpt-4o | ❌ API key | Strong tool use |
| Google | gemini-2.0-flash | ❌ API key | Fast, large context |

### Environment Compatibility Matrix

| Package | numpy 2.x | Python 3.13 | Notes |
| --- | --- | --- | --- |
| librosa 0.11 | ✅ | ✅ | Core analysis — works today |
| sqlite-vec 0.1.7 | ✅ | ✅ | C extension — installed ✅ |
| pydantic-ai 1.x | ✅ | ✅ | Agent framework — installed ✅ |
| sentence-transformers 3.x | ✅ | ✅ | Text embeddings — optional |
| HuggingFace ClapModel | ✅ | ✅ | Via `transformers ≥4.40` |
| laion-clap 1.1.7 | ❌ (needs <2.0) | ⚠️ | Use conda env: python=3.11 |
| madmom 0.16.1 | ❌ (needs <2.0) | ❌ (Cython build fail) | Use conda env: python=3.11 |

---

## 7. Sprint Planning

### Near-Term Sprints — Completing Phases 5–7 (8 Weeks)

| Sprint | Weeks | Phase | Key Deliverables |
| --- | --- | --- | --- |
| 1 | 1–2 | Phase 5 | `stats`/`duplicates` CLI commands, `--workers`, shell completion |
| 2 | 3–4 | Phase 6 | SSE import progress, HTMX live search, Wavesurfer waveform |
| 3 | 5–6 | Phase 7 | Svelte 5 + Vite scaffold, SampleTable, Rust import commands |
| 4 | 7–8 | Phase 12 | CLAP encoder, sqlite-vec ANN index, `search --semantic` |

### Quarterly Roadmap — Phases 8–13 (2026 Q3 → 2027 Q4)

| Quarter | Phase | Focus | Critical Path |
| --- | --- | --- | --- |
| Q3 2026 | 8 | FL Studio filesystem + AppleScript + MIDI | macOS entitlements |
| Q4 2026 | 9 | JUCE 8 VST3/AU plugin | CMake, sidecar IPC, auval validation |
| Q4 2026 | 11 | Production release | signing, notarization, GitHub Actions |
| Q1 2027 | 10 | Sample packs | .smpack format, SHA-256 manifest |
| Q2 2027 | 13 | AI Agent CLI + API | pydantic-ai tools, Ollama offline, `agent ask` |
| Q3 2027 | — | v1.0 release | full feature parity + semantic search + agents |

### Phase Completion Gate Criteria

Each phase must achieve before moving to the next:

- All deliverables from the phase doc implemented
- New code has type hints on public functions
- pytest coverage target met (see [Testing & Quality](#9-testing--quality))
- `uv run ruff check src/` — zero errors
- `cargo clippy -- -D warnings` — zero warnings
- CI green on all 4 matrix jobs

---

## 8. Long-Term Vision (2027–2030)

### AI & Intelligence (2027–2028)

- **Semantic search live** (Phase 12) — CLAP embeddings + sqlite-vec ANN; query *any* description
- **AI agent CLI** (Phase 13) — pydantic-ai + Ollama; auto-tag, Q&A, project-aware suggestions
- **ML-based classifier** — Replace rule-based thresholds with scikit-learn RandomForest
  trained on a labeled dataset; retrain via `samplemind train --data labeled_samples.csv`
- **Beat-aware analysis** — madmom RNN downbeat tracker (conda env: python=3.11, numpy=1.26)
- **Loop point detection** — Detect seamless loop start/end using spectral autocorrelation
- **Quality scorer** — LUFS, true peak, dynamic range, clipping detection → 0–100 score
- **Source separation** — Demucs v5+ stem splitting (vocals/drums/bass/other) inside SampleMind

### Platform Expansion (2028–2029)

- **Windows COM automation** — `win32com.client` alternative to AppleScript on Windows
- **Ableton Live support** — Filesystem export + User Library path detection
- **Deep-link URL scheme** — `samplemind://import?path=...` for browser/finder import
- **Tauri Mobile** — iOS + Android companion app (Tauri Mobile stable 2028)
- **Python 3.14 free-threaded** — PEP 703 no-GIL: true parallel librosa workers (2028)
  `ProcessPoolExecutor` → `ThreadPoolExecutor` with 4–8× speedup on multi-core

### Cloud & Community (2028–2030)

- **SampleMind Cloud** — FastAPI on cloud + PostgreSQL + pgvector; sync, backup, collaborate
- **Sample pack registry** — JSON index on GitHub Pages; in-app one-click pack browser
- **Pack marketplace** — Stripe payments for premium packs; creator revenue share
- **Pack preview audio** — 30-second MP3 preview mixdown embedded in `.smpack`
- **AI mastering assistant** — On-device diffusion models; normalize, limit, master a sample

### On-Device AI (2029–2030)

- **Apple Silicon mlx inference** — Run Llama 3 + CLAP on Neural Engine with `mlx-lm`
- **ControlNet for audio** — AI-guided sample morphing (research → production)
- **Generative sample suggestions** — AudioBox / Stable Audio 2 integration: "generate a
  4-bar lofi loop at 85 BPM in C minor based on your library style"

---

## 9. Performance Targets & SLAs

| Operation | Target | Current State | Blocker / Phase |
| --- | --- | --- | --- |
| Single file analysis (librosa) | < 500ms | ~800ms | lazy import + mtime cache (Phase 5) |
| Batch import 100 files | < 30s | Sequential | `--workers N` ProcessPoolExecutor (Phase 5) |
| Keyword search query | < 50ms | Full table scan | FTS5 virtual table (Phase 5) |
| **Semantic search (vector ANN)** | **< 50ms** | **Not built** | **sqlite-vec + CLAP (Phase 12)** |
| CLAP embedding (per file) | < 2s GPU / < 8s CPU | Not built | Phase 12 (one-time, cached) |
| **Agent response (local Ollama)** | **< 5s** | **Not built** | **pydantic-ai + llama3.3 (Phase 13)** |
| Agent response (Claude API) | < 2s | Not built | Phase 13 |
| Tauri cold start | < 2s | On track | — |
| Sidecar startup | < 3s | Not built | PyInstaller (Phase 11) |
| VST3 UI open | < 200ms | Not started | JUCE (Phase 9) |
| Pack export 100 samples | < 10s | Not built | Phase 10 |
| Pack import 100 samples | < 15s | Not built | Phase 10 |

---

## 10. Testing & Quality

### Coverage Targets

| Module | Target | Strategy |
| --- | --- | --- |
| `analyzer/` | 80%+ | `@pytest.mark.slow` on librosa tests; synthetic WAV fixtures |
| `classifier.py` | 90%+ | fast, parameterized synthetic inputs |
| `cli/` | 70%+ | Typer `CliRunner`; `--json` output assertions |
| `data/repositories/` | 85%+ | in-memory SQLite (`StaticPool`) |
| `core/auth/` | 90%+ | JWT/RBAC unit tests — 24 tests live |
| `web/` | 70%+ | Flask test client |
| `packs/` | 80%+ | `tmp_path` roundtrip |
| `analyzer/embeddings.py` | 70%+ | Mock CLAP model for speed; Phase 12 |
| `agents/` | 60%+ | pydantic-ai `TestModel`; no real API calls in CI |

### Test Pyramid (2026 strategy)

```
         ┌───────────────┐
         │  E2E (Tauri)  │  ← Phase 7+ (Playwright / WebdriverIO)
         └───────────────┘
        ┌─────────────────┐
        │  Integration    │  ← CLI CliRunner, Flask test client, Alembic check
        └─────────────────┘
      ┌─────────────────────┐
      │  Unit               │  ← pytest + hypothesis (property-based fuzzing)
      └─────────────────────┘
```

### Property-Based Tests (hypothesis — installed ✅)

```python
from hypothesis import given, strategies as st
from samplemind.data.repositories.sample_repository import SampleRepository

@given(st.text(min_size=1, max_size=255), st.floats(min_value=60, max_value=200))
def test_upsert_never_crashes(filename, bpm):
    """Property: any valid filename/BPM combination should upsert cleanly."""
    data = SampleCreate(filename=filename, path=f"/test/{filename}", bpm=bpm)
    sample = SampleRepository.upsert(data)
    assert sample.bpm == bpm

@given(st.text(min_size=3, max_size=100))
def test_search_never_raises(query):
    """Property: any search query should return a list, never raise."""
    results = SampleRepository.search(query=query)
    assert isinstance(results, list)
```

### Test Markers

```python
@pytest.mark.slow        # > 1s real librosa analysis — skipped in fast CI
@pytest.mark.macos       # AppleScript, auval, AU validation — macOS runner only
@pytest.mark.juce        # JUCE plugin built (Phase 9+)
@pytest.mark.ai          # requires Ollama running or ANTHROPIC_API_KEY
@pytest.mark.embeddings  # requires CLAP model downloaded (~1.5GB)
```

### CI Matrix

| Job | Runner | What runs |
| --- | --- | --- |
| Python (ubuntu) | ubuntu-latest | `ruff check` + `pyright` + `pytest` + `coverage` + `alembic check` |
| Python (Windows) | windows-latest | `pytest -m "not slow and not macos and not ai"` |
| Python (macOS) | macos-14 | `pytest -m "not ai and not embeddings"` (smoke test) |
| Rust | ubuntu-latest | `cargo clippy -D warnings` + `cargo test` |

### Audio Fixtures (synthetic only — never commit real WAV files)

```python
# From tests/conftest.py — already implemented
silent_wav    # 1s silence (soundfile + numpy zeros)
kick_wav      # 0.5s 60Hz sine (low-frequency, high amplitude)
hihat_wav     # 0.1s seeded white noise
orm_engine    # in-memory SQLite with StaticPool (users + samples tables)
test_user     # User fixture via UserRepository
access_token  # JWT access token for authenticated test requests
```

---

## 11. Technical Debt

### High Priority (Resolve Immediately)

1. **`src/main.py` legacy entrypoint** — Still required by `app/src-tauri/src/main.rs`
   in dev mode. Must be removed when Phase 7 (Svelte 5) lands.

2. **`samplemind-server.spec` entry point** — References `src/main.py`; must migrate to
   `src/samplemind/sidecar/server.py` before Phase 11 production build.

3. **database.py still present** — The legacy sqlite3 `database.py` is now unused by
   CLI and web (replaced by SampleRepository in Phase 4). Remove in Phase 5.

### Medium Priority (Address in Respective Phases)

1. **`app/src-tauri/capabilities/default.json`** — Exists as empty skeleton; needs
   command entries as each Rust command is added (Phase 7).

2. **`app/vite.config.ts` missing** — Svelte 5 frontend not scaffolded. Phase 7 first task.

3. **CLAP environment isolation** — CLAP (laion-clap 1.1.7) requires numpy<2.0 and
   Python ≤3.11. Document conda env setup and add `scripts/setup_clap_env.sh`.

4. **`pyright` errors** — pydantic-ai and sqlite-vec stubs may have missing type info.
   Add `# type: ignore` only at the call site with a comment explaining why.

### Low Priority (Backlog)

1. **`plugin/` directory missing** — Phase 9 starting point; scaffold `CMakeLists.txt`.

2. **Norwegian docs gap** — `docs/no/` missing `remote_inference.md` translation.

3. **`scripts/start.sh` is empty** — Either implement or delete.

4. **Alembic `check` not in CI** — Add `uv run alembic check` as a CI job step to
   detect schema drift between models and migrations automatically.

---

## 12. Risk Management

| Risk | Probability | Impact | Mitigation |
| --- | --- | --- | --- |
| JUCE build complexity on macOS | High | Medium | Phase 9 doc: step-by-step `auval` checklist |
| Tauri IPC contract drift as CLI evolves | Medium | High | JSON schema in ARCHITECTURE.md; `--json` smoke tests in CI |
| librosa cold-import latency (~800ms) | High | Medium | Lazy import + `mtime` cache (Phase 5) |
| macOS signing pipeline failure | Medium | High | Phase 11: GitHub Secrets checklist; macOS CI runner |
| PyInstaller sidecar binary bloat | Medium | Medium | `--onefile` + UPX; measure in CI artifact size check |
| FL Studio AppleScript permission denied | Low | High | `entitlements.plist` in place; accessibility prompt on first run |
| WSL2 NTFS path contamination | Medium | Low | `git config core.fsmonitor true`; CI enforces Linux paths |
| Legacy `src/main.py` breakage | Medium | High | Never remove without coordinating with Tauri `main.rs` |
| **CLAP numpy<2.0 conflict** | **High** | **Medium** | **Use HuggingFace ClapModel (numpy 2.x compat) instead of laion-clap** |
| **Ollama not running (offline agent)** | **High** | **Low** | **Graceful fallback to rule-based search; clear error message** |
| **pydantic-ai API instability** | **Medium** | **Medium** | **Pin to `pydantic-ai>=1.0,<2.0`; review changelog on upgrade** |
| **sqlite-vec ANN accuracy at scale** | **Low** | **Medium** | **Benchmark KNN recall at 10K / 100K vectors; tune index params** |
| **LLM hallucination in agent answers** | **Medium** | **Medium** | **Structured outputs only (Pydantic models); no free-form string answers** |

---

## 13. Contribution Guide

### First-Time Setup

```bash
# Clone and bootstrap
git clone https://github.com/lchtangen/SampleMind-AI
cd SampleMind-AI
uv sync --dev                       # install Python 3.13 + all core + dev deps
# Optional: uv sync --dev --extra ai   (sentence-transformers ~2 GB)
cd app && pnpm install && cd ..     # install Node deps for Tauri
pre-commit install                  # wire up ruff + pyright pre-commit hooks
git config core.fsmonitor true      # WSL2: faster git status

# Database migrations (required before first run)
uv run alembic upgrade head

# OPTIONAL: AI agent (offline — requires Ollama)
ollama pull qwen2.5-coder:7b        # fast, 8GB RAM
uv run samplemind agent ask "show library stats"

# OPTIONAL: Set up CLAP environment (separate conda env due to numpy<2.0)
conda create -n samplemind-clap python=3.11
conda activate samplemind-clap
pip install "numpy<2.0" torch torchaudio laion-clap
```

### Daily Workflow

```bash
# Python
uv run samplemind --help
uv run pytest tests/ -m "not slow" -v
uv run pytest tests/test_audio_analysis.py::test_bpm -v  # single test
uv run pytest tests/ --hypothesis-seed=0 -v              # fixed seed for reproducibility
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pyright src/                                       # type checking
uv run alembic check                                      # schema drift check

# Rust + Tauri
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cd app && pnpm tauri dev             # Tauri with HMR
```

### Branch Naming

```text
phase-02/batch-import
phase-03/sqlmodel-migration
fix/classifier-hihat-threshold
docs/update-phase-05
```

### Code Conventions

- **Python:** ruff ≥0.15 only (not black, flake8, isort, pylint)
- **Type hints:** required on all new public functions — pyright-compatible
- **Type checking:** `uv run pyright src/` — must be clean before PR
- **Imports:** `from samplemind.analyzer.audio_analysis import analyze_file` (src-layout)
- **Rust:** owned types in async commands (`String`, not `&str`); all clippy warnings fixed
- **IPC:** JSON → stdout; human text → stderr; **never mix** (this breaks Tauri IPC)
- **Audio tests:** synthetic WAV fixtures only; never commit real audio files
- **AI tests:** use `pydantic-ai TestModel` — no real API calls in CI
- **Dependencies:** `uv add <package>` (not `pip install`)
- **Frontend:** `pnpm` in `app/` (not npm)
- **Agents:** always return Pydantic models from tools; no raw string outputs

### Task Difficulty

- **Easy (1–2h):** Add type hints, expand conftest fixtures, write a single test
- **Medium (3–6h):** New CLI command, Flask endpoint, Svelte component
- **Hard (6h+):** SQLModel migration, Tauri command + Svelte binding, JUCE C++ work

### Key Files

| File | Role |
| --- | --- |
| `src/samplemind/cli/app.py` | Typer app — all CLI commands registered here |
| `src/samplemind/analyzer/audio_analysis.py` | librosa feature extraction |
| `src/samplemind/analyzer/classifier.py` | energy/mood/instrument classifiers |
| `src/samplemind/core/models/sample.py` | Sample SQLModel + SampleCreate/Update/Public |
| `src/samplemind/core/models/user.py` | User SQLModel + auth schemas |
| `src/samplemind/data/orm.py` | SQLModel engine, WAL PRAGMAs, init_orm() |
| `src/samplemind/data/repositories/sample_repository.py` | SampleRepository (CRUD + search) |
| `src/samplemind/data/repositories/user_repository.py` | UserRepository (auth CRUD) |
| `src/samplemind/core/auth/` | JWT, bcrypt, RBAC, FastAPI dependencies |
| `src/samplemind/api/routes/auth.py` | FastAPI auth routes (/register /login /me) |
| `app/src-tauri/src/main.rs` | Tauri entry point, IPC commands, JWT token store |
| `migrations/versions/` | Alembic migration history |
| `tests/conftest.py` | WAV fixtures, in-memory SQLite, auth fixtures |
| `tests/test_auth.py` | 24 auth tests (JWT, RBAC, bcrypt) |
| `.github/workflows/python-lint.yml` | CI: ruff + pyright + pytest + alembic check |
| `ARCHITECTURE.md` | System diagram and IPC contracts |
| `ROADMAP.md` | Full phase roadmap (all 13+ phases) |
| `CLAUDE.md` | Claude Code project guide |

---

*SampleMind AI — Analyze. Organize. Semantically Search. Automate with Agents. Ship.*
*Last updated: 2026-03-25 — v0.2.0*
