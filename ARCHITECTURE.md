# SampleMind AI — Architecture

> Reference document for system architecture, data flow, IPC contracts, phase roadmap, and
> technology decisions. Kept in sync with the actual codebase — not aspirational.
> **Last updated: 2026-03-26 (v0.6.0, Phases 5–7, 9, 11–14 complete)**

---

## Phase Status Dashboard

| Phase | Name | Status | Complete |
|-------|------|--------|---------|
| 1 | Foundation (uv, src-layout, config, logging) | ✅ Live | 100% |
| 2 | Audio Analysis (librosa, 8 features, classifiers) | ✅ Live | 100% |
| 3 | Database & Auth (SQLModel, Alembic, JWT, RBAC) | ✅ Live | 100% |
| 4 | CLI Modernization (Typer, batch, FTS5, perf) | ✅ Live | 100% |
| 5 | Web UI (Flask HTMX, SSE, blueprints) | ✅ Live | 100% |
| 6 | Desktop App (Svelte 5, Tauri IPC commands) | ✅ Live | 100% |
| 7 | FL Studio Integration (filesystem, AppleScript, MIDI) | ✅ Live | 100% |
| 8 | VST3/AU Plugin (JUCE 8, sidecar) | 🔄 Partial | 90% |
| 9 | Sample Packs (.smpack ZIP, SHA-256, distribution) | ✅ Live | 100% |
| 10 | Production Release (signing, notarization, CI/CD) | 📋 Planned | 0% |
| 11 | Semantic Search (CLAP embeddings, FAISS/sqlite-vec) | ✅ Live | 96% |
| 12 | AI Curation (pydantic-ai, LiteLLM, smart playlists) | ✅ Live | 95% |
| 13 | Cloud Sync (R2/Supabase, multi-device CRDTs) | 🔄 Partial | 90% |
| 14 | Analytics Dashboard (Plotly, BPM histograms) | ✅ Live | 100% |
| 15 | Marketplace (Stripe, pack listings, signed CDN) | 🔄 Partial | 70% |
| 16 | AI Generation (AudioCraft, Stable Audio, text-to-audio) | ✅ Live | 90% |

**Overall project progress: ~85%** — Phases 1–9, 11–14 fully live; 8, 13, 15–16 partial; 10 planned.

---

## System Layers

```text
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4 — DAW Integration                          [Phase 7-8] │
│  ┌──────────────────────┐   ┌─────────────────────────────────┐ │
│  │  JUCE Plugin (C++)   │   │  FL Studio (macOS / Windows)    │ │
│  │  VST3 + AU           │   │  - Filesystem browser           │ │
│  │  PluginEditor UI     │   │  - AppleScript automation       │ │
│  │  PythonSidecar IPC   │   │  - Virtual MIDI (IAC Driver)    │ │
│  └──────────┬───────────┘   └─────────────────────────────────┘ │
└─────────────┼───────────────────────────────────────────────────┘
              │ Unix domain socket (~/tmp/samplemind.sock)
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 3 — Desktop Application (Tauri 2)           [Phase 6]   │
│  ┌──────────┴──────────┐                                        │
│  │  Svelte 5 + Vite    │  Components (Phase 6 target):          │
│  │  (WKWebView macOS)  │  SampleTable, ImportPanel,             │
│  │  app/src/main.ts    │  WaveformPlayer, SearchBar             │
│  └──────────┬──────────┘                                        │
│             │ tauri::invoke() IPC                               │
│  ┌──────────┴──────────┐                                        │
│  │  Rust (Tauri core)  │  Live commands (5):                    │
│  │  app/src-tauri/     │  pick_folder, is_directory,            │
│  │  src/main.rs        │  store_token, get_token, clear_token   │
│  │                     │  + system tray + Flask spawning        │
│  └──────────┬──────────┘                                        │
│             │ Dev: spawns Flask at :5174                        │
│             │ Prod: PyInstaller sidecar binary                  │
└─────────────┼───────────────────────────────────────────────────┘
              │ stdout JSON (samplemind import --json ...)
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 2 — Python Backend                                       │
│  ┌──────────┴──────────┐                                        │
│  │  Typer CLI          │  21 commands: import, analyze, list,   │
│  │  src/samplemind/    │  search, tag, serve, api, duplicates,  │
│  │  cli/app.py         │  export, stats, health, version,       │
│  │                     │  sidecar, export-to-fl, midi-sync,     │
│  │                     │  pack, sync, similar, curate,          │
│  │                     │  analytics, generate                   │
│  └──────────┬──────────┘                                        │
│             │                                                   │
│  ┌──────────┴────────────────────────────────────────────────┐  │
│  │  Core Services                                            │  │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ Audio Analysis   │  │ Data Layer                   │  │  │
│  │  │ librosa 0.11     │  │ SQLModel + Alembic            │  │  │
│  │  │ 8 features       │  │ SampleRepository             │  │  │
│  │  │ batch.py workers │  │ UserRepository               │  │  │
│  │  │ fingerprint.py   │  │ FTS5 virtual table           │  │  │
│  │  └──────────────────┘  └──────────────────────────────┘  │  │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ Flask Web UI     │  │ FastAPI (auth server)        │  │  │
│  │  │ HTMX + SSE       │  │ JWT + RBAC                   │  │  │
│  │  │ [Phase 5]        │  │ /api/v1/auth/*               │  │  │
│  │  └──────────────────┘  └──────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 1 — Storage                                              │
│  ┌──────────┴──────────┐   ┌──────────────────────────────────┐ │
│  │  SQLite DB (WAL)     │   │  Audio Files                     │ │
│  │  ~/Library/          │   │  (WAV/AIFF — original paths      │ │
│  │  Application         │   │   preserved; never copied)       │ │
│  │  Support/SampleMind/ │   │                                  │ │
│  └─────────────────────┘   └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```text
WAV / AIFF file on disk
     │
     ▼
fingerprint_file()          ← SHA-256 of first 64 KB (dedup check before analysis)
     │ duplicate? skip
     ▼
librosa.load(sr=22050)      ← scipy FFT backend, soxr_hq resampling
     │
     ▼
Feature extraction (8 features per file)
  rms                   ← amplitude (energy proxy)
  spectral_centroid     ← brightness, normalized to Nyquist (0–1)
  zero_crossing_rate    ← texture (hihat ≈ 0.35, kick ≈ 0.03)
  spectral_flatness     ← noise vs. tone (0 = sine, 1 = white noise)
  spectral_rolloff      ← 85% energy frequency, normalized
  onset_mean / max      ← rhythmic attack strength
  low_freq_ratio        ← bass presence below 300 Hz
  duration              ← file length in seconds
     │
     ▼
Classification (3 independent rule-based classifiers)
  classify_energy()     → "low" | "mid" | "high"
  classify_mood()       → "dark" | "chill" | "aggressive" | "euphoric" | "melancholic" | "neutral"
  classify_instrument() → "kick" | "snare" | "hihat" | "bass" | "pad" | "lead" | "loop" | "sfx" | "unknown"
     │
     ▼
SampleRepository.upsert()   ← data/repositories/sample_repository.py (SQLModel)
     │   Auto-detected fields overwritten on re-import.
     │   User tags (genre, tags) are NEVER overwritten.
     ▼
SQLite (platformdirs: ~/Library/Application Support/SampleMind/samplemind.db on macOS)

  users table (13 columns — migration 0001):
    id, user_id (UUID), email, username, hashed_password,
    role, is_active, is_verified, created_at, updated_at,
    last_login, total_analyses

  samples table (12 columns — migration 0002):
    id, filename, path (UNIQUE), bpm, key, mood, genre,
    energy, tags, instrument, imported_at

  samples_fts (FTS5 virtual table — migration 0003, LIVE):
    Content table on (filename, tags, genre)
    Auto-sync triggers: AFTER INSERT / UPDATE / DELETE on samples

  WAL mode + 5 performance PRAGMAs on every connection (via SQLAlchemy event listener):
    journal_mode=WAL  cache_size=-64000  synchronous=NORMAL
    temp_store=MEMORY  mmap_size=268435456

     │
     ├──► Typer CLI (stdout JSON for Tauri IPC)
     ├──► Flask Web UI (HTMX partials, SSE progress)
     ├──► FastAPI auth server (/api/v1/*)
     ├──► Tauri Desktop App (invoke() commands → subprocess stdout)
     ├──► FL Studio export (filesystem, clipboard, MIDI) [Phase 7]
     ├──► JUCE Plugin (via Python sidecar socket) [Phase 8]
     └──► .smpack pack export / import [Phase 9]
```

---

## IPC Contract Table

### Current Live State (Phase 1–4 runtime)

The Tauri app loads Flask web UI in a WebView at `http://127.0.0.1:5174`. Rust handles OS tasks
and in-memory JWT token storage. Python logic flows via HTTP — not subprocess calls yet.

| Tauri Command (Rust) | Purpose | Return type |
|---|---|---|
| `pick_folder` | Native folder picker dialog (tauri-plugin-dialog) | `Option<String>` |
| `is_directory` | Check if a path is a directory on disk | `bool` |
| `store_token` | Store a JWT access token in `AuthTokenStore` (Mutex-protected) | `()` |
| `get_token` | Retrieve the stored token, if any | `Option<String>` |
| `clear_token` | Clear the stored token (logout) | `()` |

Flask serves at port 5174 (Tauri-spawned, dev mode) or 5000 (`samplemind serve` standalone).
Release mode uses a PyInstaller sidecar binary (`binaries/samplemind-server`).

### Target State (Phase 6+ — Svelte frontend replaces WebView)

Once Svelte 5 components are built, Tauri will call Python via subprocess stdout JSON:

| Tauri Command (Rust) | Python CLI Invocation | JSON Response Schema |
|---|---|---|
| `import_folder` | `samplemind import <path> --json` | `{"imported": N, "errors": M}` |
| `search_samples` | `samplemind search <query> --json` | `[{"filename": S, "bpm": F, ...}]` |
| `analyze_file` | `samplemind analyze <path> --json` | `{"bpm": F, "key": S, "energy": S, "mood": S, "instrument": S}` |
| `get_stats` | `samplemind list --json` | `[{"filename": S, ...}]` |
| `get_duplicates` | `samplemind duplicates --json` | `{"groups": [[path, ...], ...]}` |

### `analyze` JSON Output (Phase 4 runtime)

`samplemind analyze <path> --json` writes exactly these 5 fields to **stdout**:

```json
{
  "bpm": 128.0,
  "key": "C min",
  "energy": "mid",
  "mood": "dark",
  "instrument": "kick"
}
```

### Database Row Schema (samples table — v0.2.0)

```json
{
  "id": 42,
  "filename": "kick_128bpm.wav",
  "path": "/Users/name/Music/Samples/kick_128bpm.wav",
  "bpm": 128.0,
  "key": "C min",
  "mood": "dark",
  "genre": "trap",
  "energy": "mid",
  "tags": "808,heavy",
  "instrument": "kick",
  "imported_at": "2026-03-25T12:00:00"
}
```

> `energy` is always `low` / `mid` / `high` — never `"medium"`. Tags are a comma-separated string,
> not a JSON array. There is no `duration` column in the schema.

### Python Sidecar Socket Protocol (JUCE Plugin — Phase 8)

Length-prefixed JSON over a Unix domain socket (`~/tmp/samplemind.sock`):

```text
Request:  [4-byte big-endian int: length] [UTF-8 JSON bytes]
Response: [4-byte big-endian int: length] [UTF-8 JSON bytes]

Supported actions (version 2 envelope):
  {"version": 2, "action": "ping"}
  {"version": 2, "action": "search", "query": "...", "energy": "...", "instrument": "..."}
  {"version": 2, "action": "analyze", "path": "/absolute/path/to/file.wav"}
  {"version": 2, "action": "batch_analyze", "paths": [...]}
```

---

## Component Responsibilities

| Component | Location | Status | Responsibility |
|---|---|---|---|
| **Audio Analyzer** | `src/samplemind/analyzer/audio_analysis.py` | ✅ Live | librosa BPM + key detection; 8 feature vectors; `analyze_file()` |
| **Batch Processor** | `src/samplemind/analyzer/batch.py` | ✅ Live | `analyze_batch()` — ProcessPoolExecutor parallel analysis, `workers=0` = auto CPU |
| **Classifier** | `src/samplemind/analyzer/classifier.py` | ✅ Live | Rule-based: energy (low/mid/high), mood (6 values), instrument (9 values) |
| **Fingerprinter** | `src/samplemind/analyzer/fingerprint.py` | ✅ Live | `fingerprint_file()` — SHA-256 of first 64 KB; `find_duplicates()` |
| **SQLModel ORM** | `src/samplemind/data/orm.py` | ✅ Live | `get_engine()`, `init_orm()`, `get_session()` context manager; 5 WAL PRAGMAs via event |
| **SampleRepository** | `src/samplemind/data/repositories/sample_repository.py` | ✅ Live | upsert, search (FTS5 + LIKE fallback), tag, get_by_name/path/id, count, delete |
| **UserRepository** | `src/samplemind/data/repositories/user_repository.py` | ✅ Live | create, get_by_email/username/id, update, record_login, deactivate |
| **Auth — JWT** | `src/samplemind/core/auth/jwt_handler.py` | ✅ Live | `create_access_token()`, `create_refresh_token()`, `decode_token()`, `verify_token()` |
| **Auth — Password** | `src/samplemind/core/auth/password.py` | ✅ Live | bcrypt hash (cost 12+), verify, needs_rehash |
| **Auth — RBAC** | `src/samplemind/core/auth/rbac.py` | ✅ Live | `UserRole` enum (4 roles), `Permission` enum (16 perms), `RBACService` |
| **Auth — API Keys** | `src/samplemind/core/auth/api_keys.py` | ✅ Live | `APIKeyService` — scoped tokens (`sm_live_` / `sm_test_` prefixed), SHA-256 stored |
| **Auth — Dependencies** | `src/samplemind/core/auth/dependencies.py` | ✅ Live | FastAPI `Depends()` helpers: `get_current_user()`, `get_current_active_user()` |
| **Config** | `src/samplemind/core/config.py` | ✅ Live | `Settings` (pydantic-settings), `get_settings()` (lru_cache), platformdirs DB path |
| **Health** | `src/samplemind/core/health.py` | ✅ Live | Structured health check: DB connectivity, table presence, sample count |
| **Logging** | `src/samplemind/core/logging.py` | ✅ Live | structlog configuration; JSON renderer in prod, dev renderer locally |
| **FastAPI App** | `src/samplemind/api/main.py` | ✅ Live | `create_app()` factory; lifespan (init_orm + configure_jwt); CORS; /api/v1/health |
| **Auth Routes** | `src/samplemind/api/routes/auth.py` | ✅ Live | /register, /login, /refresh, /logout, /me (GET/PUT), /change-password |
| **Typer CLI** | `src/samplemind/cli/app.py` | ✅ Live | 21 commands; `--json` on all data commands; JSON → stdout, human text → stderr |
| **CLI: import** | `src/samplemind/cli/commands/import_.py` | ✅ Live | Discover WAV files → `analyze_batch()` → upsert → Rich table or JSON |
| **CLI: analyze** | `src/samplemind/cli/commands/analyze.py` | ✅ Live | Analyze without storing; useful for preview / IPC testing |
| **CLI: library** | `src/samplemind/cli/commands/library.py` | ✅ Live | `list` + `search` with all filters; Rich table or JSON |
| **CLI: tag** | `src/samplemind/cli/commands/tag.py` | ✅ Live | Update genre/mood/energy/tags by partial filename match |
| **CLI: export** | `src/samplemind/cli/commands/export.py` | ✅ Live | Dump library to JSON or CSV file |
| **CLI: duplicates** | `src/samplemind/cli/commands/duplicates.py` | ✅ Live | Find SHA-256 duplicate groups; optionally remove from disk + DB |
| **CLI: stats** | `src/samplemind/cli/commands/stats.py` | ✅ Live | Summary: total, BPM range, key/mood/energy/instrument distributions |
| **CLI: health** | `src/samplemind/cli/commands/health.py` | ✅ Live | DB health check, table existence, sample count |
| **CLI: serve / api** | `src/samplemind/cli/commands/serve.py`, `api.py` | ✅ Live | Launch Flask :5000 or FastAPI :8000 |
| **Flask Web UI** | `src/samplemind/web/app.py` | 🔄 Partial | `create_app()` factory; blueprints: library_bp, import_bp |
| **Web Blueprints** | `src/samplemind/web/blueprints/` | 🔄 Partial | `library.py` (list/search routes), `import_.py` (upload routes) |
| **Tauri Rust Core** | `app/src-tauri/src/main.rs` | ✅ Live | 5 IPC commands; Flask spawning (dev) / sidecar binary (prod); system tray |
| **Svelte Frontend** | `app/src/main.ts` | 🔄 Partial | Entry point boots Svelte App; full components target Phase 6 |
| **ML Model Loader** | `src/samplemind/utils/model_loader.py` | ✅ Live | Low-memory HuggingFace loading (8-bit quant, disk offload, remote fallback) |
| **FL Studio Export** | `src/samplemind/integrations/` | ✅ Live | Filesystem copy, AppleScript automation, clipboard path copy, MIDI BPM sync |
| **Pack System** | `src/samplemind/packs/` | ✅ Live | .smpack ZIP format; manifest.json; SHA-256 integrity; CLI pack create/import/list |
| **Python Sidecar** | `src/samplemind/sidecar/` | 📋 Phase 8 | asyncio Unix socket server for JUCE plugin IPC |
| **JUCE Plugin** | `plugin/Source/` | 📋 Phase 8 | VST3 + AU plugin; PluginEditor; PythonSidecar IPC client |
| **Semantic Search** | `src/samplemind/search/` | ✅ Live | 10-dim audio embeddings; 384-dim text (MiniLM); sqlite-vec vector index; CLI similar |
| **AI Curation** | `src/samplemind/agent/` | ✅ Live | pydantic-ai CuratorAgent; playlist_by_energy; gap_analysis; CLI curate analyze/playlist/gaps |
| **Cloud Sync** | `src/samplemind/sync/` | 🔄 Partial | boto3 S3-compatible push/pull; MD5/ETag dedup; CLI sync push/pull/status |
| **Analytics** | `src/samplemind/analytics/` | ✅ Live | LibrarySummary; BPM buckets; key counts; growth timeline; CLI analytics |
| **Legacy DB** | `src/samplemind/data/database.py` | ⚠️ Deprecated | sqlite3 functions; kept for reference only; do not add new imports |

---

## 16-Phase Roadmap

| Phase | Name | Priority | Effort | Success Rate | Key Deliverable |
|-------|------|----------|--------|-------------|-----------------|
| 1 | Foundation | — | Done | 100% | uv, pyproject.toml, src-layout, structlog, pydantic-settings |
| 2 | Audio Analysis | — | Done | 100% | librosa 0.11, 8 features, classifiers, WAV fixtures |
| 3 | Database & Auth | — | Done | 100% | SQLModel, Alembic, JWT, RBAC, SampleRepository |
| 4 | CLI Modernization | — | Done | 100% | Typer 12 commands, batch workers, FTS5, fingerprinting |
| 5 | Web UI | P1 | 5d | 97% | Flask HTMX live search, SSE import progress, waveform player |
| 6 | Desktop App | P1 | 10d | 96% | Svelte 5 Runes components, Tauri IPC, .dmg/.msi builds |
| 7 | FL Studio | P2 | 7d | 95% | Filesystem export, AppleScript, IAC MIDI clock |
| 8 | VST3/AU Plugin | P2 | 14d | 93% | JUCE 8 plugin, Python sidecar Unix socket |
| 9 | Sample Packs | P3 | 5d | 98% | .smpack ZIP, manifest.json, SHA-256, pack CLI commands |
| 10 | Production Release | P0 | 10d | 94% | Apple Developer ID, notarization, Azure signing, release CI/CD |
| 11 | Semantic Search | P2 | 8d | 96% | CLAP embeddings, sqlite-vec vector index, "find similar" |
| 12 | AI Curation | P2 | 10d | 95% | pydantic-ai agent, LiteLLM, smart playlists, gap analysis |
| 13 | Cloud Sync | P3 | 12d | 93% | Cloudflare R2 / Supabase, CRDT conflict resolution |
| 14 | Analytics | P2 | 6d | 97% | Plotly BPM histograms, key heatmaps, growth timeline |
| 15 | Marketplace | P3 | 14d | 92% | Stripe checkout, pack listings, signed CDN URLs, ratings |
| 16 | AI Generation | P2 | 12d | 94% | AudioCraft / Stable Audio, text-to-audio, .samplemind.json |

**Critical path:** Phase 4 → Phase 5 → Phase 6 → Phase 10 (core app release).
Phases 7–8 depend on Phase 6. Phase 9 depends on Phase 4. Phases 11–16 depend on Phase 4.

**Full timeline:** ~22 weeks / 109 working days for all 16 phases.

---

## Repository Structure

```text
SampleMind-AI/
├── src/samplemind/                  ← Python package (src-layout, v0.2.0)
│   ├── __init__.py                  ← __version__ = "0.2.0"
│   ├── __main__.py                  ← python -m samplemind entry point
│   ├── cli/
│   │   ├── app.py                   ← Typer app; 12 commands registered
│   │   └── commands/
│   │       ├── import_.py           ← samplemind import <folder> [--workers N] [--json]
│   │       ├── analyze.py           ← samplemind analyze <file> [--json]
│   │       ├── library.py           ← samplemind list / search [filters] [--json]
│   │       ├── tag.py               ← samplemind tag <name> [--genre] [--mood] ...
│   │       ├── serve.py             ← samplemind serve / api
│   │       ├── export.py            ← samplemind export [--format json|csv]
│   │       ├── duplicates.py        ← samplemind duplicates [--remove]
│   │       ├── stats.py             ← samplemind stats
│   │       └── health.py            ← samplemind health
│   ├── analyzer/
│   │   ├── audio_analysis.py        ← analyze_file() — full librosa pipeline
│   │   ├── classifier.py            ← classify_energy/mood/instrument()
│   │   ├── fingerprint.py           ← fingerprint_file(), find_duplicates()
│   │   └── batch.py                 ← analyze_batch() — ProcessPoolExecutor
│   ├── core/
│   │   ├── config.py                ← Settings (pydantic-settings, platformdirs)
│   │   ├── health.py                ← check_health() → structured HealthResult
│   │   ├── logging.py               ← structlog setup (JSON in prod, dev renderer local)
│   │   ├── auth/
│   │   │   ├── __init__.py          ← public surface: all auth exports
│   │   │   ├── jwt_handler.py       ← create/decode/verify tokens
│   │   │   ├── password.py          ← bcrypt hash + verify
│   │   │   ├── rbac.py              ← UserRole, Permission, RBACService, ROLE_PERMISSIONS
│   │   │   ├── api_keys.py          ← APIKeyService — scoped sm_live_ / sm_test_ tokens
│   │   │   └── dependencies.py      ← FastAPI Depends: get_current_user, require_role
│   │   └── models/
│   │       ├── user.py              ← User table + UserCreate/Update/Public, TokenResponse
│   │       └── sample.py            ← Sample table + SampleCreate/Update/Public
│   ├── data/
│   │   ├── orm.py                   ← get_engine(), init_orm(), get_session(); 5 PRAGMAs
│   │   ├── database.py              ← [deprecated] legacy sqlite3; do not import in new code
│   │   └── repositories/
│   │       ├── sample_repository.py ← SampleRepository (all sample CRUD)
│   │       └── user_repository.py   ← UserRepository (create, get, update, deactivate)
│   ├── api/
│   │   ├── main.py                  ← FastAPI create_app() factory; lifespan; CORS
│   │   └── routes/
│   │       └── auth.py              ← /api/v1/auth: register, login, refresh, me
│   ├── web/
│   │   ├── app.py                   ← Flask create_app() factory; blueprint registration
│   │   ├── blueprints/
│   │   │   ├── library.py           ← GET/POST routes for sample library
│   │   │   └── import_.py           ← upload + import routes
│   │   ├── templates/               ← Jinja2: base.html, index.html, login.html
│   │   └── static/                  ← CSS + JS
│   └── utils/
│       └── model_loader.py          ← HuggingFace model loading (8-bit, offload, remote)
├── src/main.py                      ← [legacy] argparse entry; used by Tauri dev mode only
├── app/                             ← Tauri 2 desktop application
│   ├── src/
│   │   └── main.ts                  ← Svelte 5 entry point (minimal; components in Phase 6)
│   ├── src-tauri/
│   │   ├── src/
│   │   │   └── main.rs              ← 5 IPC commands; Flask spawn; tray; AuthTokenStore
│   │   ├── Cargo.toml               ← tauri 2, tauri-plugin-dialog, serde_json
│   │   ├── tauri.conf.json          ← bundle: dmg, msi, appimage; updater; CSP
│   │   ├── entitlements.plist       ← macOS sandbox entitlements
│   │   └── samplemind-server        ← PyInstaller sidecar binary (134 MB, pre-built)
│   ├── package.json                 ← pnpm workspace; Svelte 5, Tauri CLI 2, Vite 8
│   └── tsconfig.json
├── migrations/                      ← Alembic schema history
│   ├── env.py                       ← dynamic DB URL; imports all models; WAL-aware
│   └── versions/
│       ├── 0001_create_users_table.py   ← users (13 columns)
│       ├── 0002_create_samples_table.py ← samples (12 columns)
│       └── 0003_add_fts5_search.py      ← FTS5 virtual table + auto-sync triggers
├── tests/                           ← pytest suite (9 files, 33+ tests)
│   ├── conftest.py                  ← WAV fixtures, orm_engine, test_user, access_token
│   ├── test_audio_analysis.py       ← BPM, key, analyze_file() pipeline
│   ├── test_classifier.py           ← energy, mood, instrument classifiers
│   ├── test_fingerprint.py          ← fingerprint_file(), find_duplicates()
│   ├── test_auth.py                 ← JWT, bcrypt, RBAC, FastAPI auth routes (24 tests)
│   ├── test_sample_repository.py    ← upsert, search, tag, FTS5 fallback
│   ├── test_cli.py                  ← Typer CliRunner tests
│   ├── test_stats.py                ← stats command output
│   └── test_web.py                  ← Flask blueprint test client
├── docs/
│   ├── en/                          ← English phase docs (phase-01 through phase-16, +2)
│   └── no/                          ← Norwegian phase docs
├── scripts/
│   ├── setup-dev.sh                 ← bootstrap new contributors (uv, git fsmonitor, hooks)
│   └── start.sh                     ← quick-start: web | desktop | both
├── .github/workflows/
│   └── python-lint.yml              ← ruff + pyright + pytest + alembic + clippy (4 jobs)
├── ARCHITECTURE.md                  ← this file
├── MASTER_EXECUTION_INDEX.md        ← phase dashboard, next 5 tasks, agent matrix
├── PREMIUM_EXECUTION_FRAMEWORK.md  ← 16-phase roadmap, code templates, benchmarks
├── EXECUTION_PLAN.md                ← critical path, priorities, phase dependencies
├── AGENT_EXECUTION_GUIDE.md        ← agent activation workflows, slash command reference
├── PHASE_4_CHECKLIST.md            ← day-by-day Task 4.1–4.4 with acceptance criteria
├── CLAUDE.md                        ← Claude Code project guide + 19-agent routing table
├── pyproject.toml                   ← Python config (uv, ruff, pyright, pytest, coverage)
└── alembic.ini                      ← points to migrations/; ruff post-write hooks
```

---

## ML Pipeline

All batch processing is **live** as of Phase 4 (v0.2.0):

```text
Batch import flow:
files[] (discovered recursively from source path)
  │
  ├── fingerprint_file() ─────► SHA-256 dedup check → skip known files
  │
  └── analyze_batch(paths, workers=N)      ← src/samplemind/analyzer/batch.py
        │  ProcessPoolExecutor(workers)
        │  workers=0 → os.cpu_count() auto
        │  progress_cb(completed, total) for Rich progress bar
        │
        └── analyze_file(path)             ← each worker independently
              ├── librosa.load(sr=22050)
              ├── extract 8 features
              ├── classify_energy/mood/instrument()
              └── return AudioFeatures TypedDict

  └── SampleRepository.upsert(SampleCreate(...))   ← after each worker completes
```

**Graceful degradation:** per-file failures return `{"error": ..., "path": ...}` and do not
abort the batch. The import summary reports imported count + error count.

**FTS5 detection at runtime:**

```python
# SampleRepository.search() automatically uses FTS5 if migration 0003 is applied:
if SampleRepository._fts5_available(session):
    # fast: SELECT id FROM samples_fts WHERE samples_fts MATCH ?
    ...
else:
    # fallback: WHERE filename LIKE ? OR tags LIKE ? OR genre LIKE ?
    ...
```

---

## Performance Targets

| Operation | Target | Current (v0.2.0) |
|-----------|--------|-----------------|
| Single file analysis | < 500ms | ~800ms (librosa cold import on first call) |
| Batch import (100 files, 4 workers) | < 30s | ~30s with workers (sequential was 80s) |
| FTS5 search query | < 50ms | ~50ms (FTS5 live since migration 0003) |
| LIKE fallback search | < 120ms | ~120ms (if 0003 not applied) |
| Tauri cold start | < 2s | ~2s (Flask spawn adds ~1s in dev mode) |
| CLI startup | < 100ms | < 100ms (typer + rich only) |
| Sidecar startup | < 3s | N/A (Phase 8) |
| VST3 UI open | < 200ms | N/A (Phase 8) |

**Remaining bottlenecks for Phase 5:**

- Single file analysis: ~800ms first call (librosa JIT + numba cache warmup); target 500ms
  with `--skip-analysis` flag and mtime-based re-analysis cache
- Batch is now parallel, but 100-file target assumes 4+ CPU cores; single-core machines ~60s

---

## Security Model

- **No mandatory network access** — all analysis, storage, and search run locally; cloud APIs opt-in
- **JWT tokens:** access + refresh tokens stored in `AuthTokenStore` (Mutex, in-memory only) in Rust
  Tauri process; never written to disk; cleared via `clear_token` IPC on logout
- **Passwords:** bcrypt-hashed (cost 12+); plaintext never persisted or logged
- **API keys:** SHA-256 stored; plaintext shown once at creation; scoped via `APIKeyPermission`
  enum (READ, WRITE, ANALYZE, SEARCH, ADMIN); prefixed `sm_live_` / `sm_test_`
- **SQLite:** plain user-owned file; no encryption (sample library metadata, not PII)
- **Sidecar binary:** PyInstaller bundle; SHA-256 checksum verified at Tauri startup
- **Code signing:**
  - macOS: Apple Developer ID Application certificate + notarization via `xcrun notarytool`
  - Windows: Azure Trusted Signing (replaces deprecated EV certificate requirement)
- **macOS sandbox entitlements** (minimum set):
  - `com.apple.security.automation.apple-events` (AppleScript → FL Studio)
  - `com.apple.security.cs.allow-unsigned-executable-memory` (Python sidecar)
  - `com.apple.security.files.user-selected.read-write` (user file access)
  - `com.apple.security.assets.music.read-write` (Music folder)
- **Audio files:** never copied or modified unless user explicitly triggers export
- **Telemetry:** disabled by default; Sentry opt-in via `SAMPLEMIND_SENTRY_DSN` env var

---

## RBAC Permission Model

Sourced from `src/samplemind/core/auth/rbac.py` — 4 roles × 16 permissions:

| Permission | viewer | member | owner | admin |
|-----------|:------:|:------:|:-----:|:-----:|
| audio:read | ✅ | ✅ | ✅ | ✅ |
| search:basic | ✅ | ✅ | ✅ | ✅ |
| audio:write | | ✅ | ✅ | ✅ |
| audio:delete | | ✅ | ✅ | ✅ |
| audio:analyze | | ✅ | ✅ | ✅ |
| audio:batch | | ✅ | ✅ | ✅ |
| search:advanced | | ✅ | ✅ | ✅ |
| pack:create | | ✅ | ✅ | ✅ |
| pack:export | | ✅ | ✅ | ✅ |
| api:key_create | | ✅ | ✅ | ✅ |
| api:key_revoke | | | ✅ | ✅ |
| admin:user_manage | | | | ✅ |
| admin:system | | | | ✅ |

`RBACService.has_permission(role, permission)` is the canonical runtime check.
`require_permission(Permission.X)` is the FastAPI `Depends()` decorator for route protection.

---

## Observability

- **Structured logging:** `structlog` → stderr only (never stdout — preserves IPC contract)
- **Log levels:**
  - `DEBUG` — analysis feature values, import timing per file, socket messages
  - `INFO` — import counts, search results, server startup port
  - `WARNING` — missing optional deps (soxr, rtmidi), degraded mode
  - `ERROR` — analysis failures, DB write errors, sidecar crashes
- **Output format:** JSON renderer in production; colored dev renderer locally (via `core/logging.py`)
- **Sentry (opt-in, Phase 10):** crash reporting; `traces_sample_rate=0.1`; no PII captured
- **Performance metrics:** import time + analysis time logged at DEBUG per file
- **Tauri:** `tauri::api::log` for Rust-side events; forwarded to system console

```python
# Correct pattern — structlog to stderr only:
import structlog
logger = structlog.get_logger(__name__)
logger.debug("analyze.complete", path=path, duration_ms=elapsed_ms)
# NEVER: print(json_result)  ← breaks IPC contract if on stdout
# NEVER: logger.info(json.dumps(result))  ← JSON to stderr confuses parsers
```

---

## Technology Decision Log

| Technology | Replaces | Rationale |
|---|---|---|
| **uv** | pip + venv | 10–100× faster installs; single tool for packages, envs, and scripts |
| **pyproject.toml** | requirements.txt | PEP 621 standard; one file for deps, scripts, and tool config |
| **src-layout** | flat layout | Prevents accidental imports of the source tree instead of installed package |
| **pydantic-settings** | os.environ | Type-safe settings with env var, .env file, and default fallback layers |
| **structlog** | logging.basicConfig | Structured JSON/dev output; automatic field binding; no manual formatting |
| **platformdirs** | hardcoded paths | Cross-platform app data dirs; `~/.config/` on Linux, `%APPDATA%` on Windows, `~/Library/` on macOS |
| **SQLModel** | raw sqlite3 | Type-safe ORM: SQLAlchemy 2.0 + Pydantic v2 in one class |
| **Alembic** | `_migrate()` function | Versioned, reversible schema migrations; `alembic check` in CI |
| **sqlite-vec** | FAISS (external) | Embedded vector search as a SQLite extension; no external DB for Phase 11 |
| **bcrypt (direct)** | passlib[bcrypt] | passlib 1.7.x cannot parse bcrypt 4.x/5.x version strings |
| **FastAPI** | Flask (for API) | Async; auto OpenAPI docs; Pydantic v2 native validation |
| **python-jose** | PyJWT | Supports both HS256 and RS256; access + refresh token types |
| **pydantic-ai** | custom LLM wiring | Model-agnostic agent framework; structured outputs; Phase 12 |
| **sentence-transformers** | laion-clap | numpy 2.x compatible; simpler install; CLAP model via HuggingFace |
| **soxr** | librosa default resampler | Higher-quality resampling (`soxr_hq`); faster than scipy |
| **StaticPool** in tests | thread-local pools | Keeps in-memory SQLite on one connection across all threads |
| **expire_on_commit=False** | default Session | Prevents `DetachedInstanceError` on ORM objects after session close |
| **Typer + Rich** | argparse | Type annotations = automatic `--help`; Rich = beautiful terminal output |
| **HTMX** | custom JS | Replaces ~80% of hand-written JS with HTML attributes |
| **SSE (Server-Sent Events)** | polling | One-way server→browser streaming; no WebSocket overhead |
| **Tauri 2** | Electron | 3–15 MB bundle vs 120–200 MB; Rust backend; system WebView (WKWebView) |
| **Svelte 5 Runes** | Svelte 4 stores | Fine-grained reactivity; no hidden implicit dependencies |
| **JUCE 8** | — | Industry standard for audio plugins; VST3 + AU from one codebase |
| **Unix domain socket** | TCP socket | Lower latency for local IPC; no port conflict risk |
| **python-rtmidi** | — | Phase 7 FL Studio MIDI clock sync via IAC Driver |
| **PyInstaller** | requiring Python | Bundles Python sidecar as standalone binary for end-user distribution |
| **GitHub Actions** | manual builds | Reproducible CI/CD; macOS signing + notarization automated |
| **pytest + soundfile fixtures** | real audio files | Synthetic WAV generation for reproducible tests; no committed binaries |

---

## Development vs Production Topology

### Development (Windows WSL2)

```text
Windows 11
└── WSL2 (Ubuntu 24.04)
    ├── /home/ubuntu/dev/projects/SampleMind-AI/  ← ALL code here (Linux ext4, fast)
    │   ├── uv sync --dev                          ← install all deps
    │   ├── uv run samplemind import ~/Music/       ← CLI
    │   ├── uv run pytest tests/ -v                ← Python tests
    │   ├── cargo clippy --manifest-path app/src-tauri/Cargo.toml
    │   └── cd app && pnpm tauri dev               ← Tauri dev mode
    └── VS Code (Remote-WSL extension)

NOTE: NEVER store code under /mnt/c/ — NTFS is 5–10× slower for git and Python.
```

### Production (macOS)

```text
macOS 12+ (Apple Silicon preferred)
└── SampleMind.app  (Tauri bundle, ~15 MB signed + notarized)
    ├── Contents/MacOS/
    │   ├── SampleMind              ← Tauri/Rust binary (Developer ID signed)
    │   └── samplemind-server       ← PyInstaller sidecar (SHA-256 verified)
    ├── Contents/Resources/
    │   └── (Vite/Svelte build)
    └── (stapled notarization ticket from Apple)

FL Studio plugins:
    ~/Library/Audio/Plug-Ins/Components/SampleMind.component  ← AU [Phase 8]
    ~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3             ← VST3 [Phase 8]

Sample library:
    ~/Library/Application Support/SampleMind/samplemind.db  ← SQLite (WAL)
    ~/Music/SampleMind/                                      ← organized exports [Phase 7]
```

---

## Sidecar v2 Architecture (Phase 8)

```text
JUCE Plugin                    Python Sidecar (PyInstaller bundle)
┌─────────────────┐            ┌──────────────────────────────────────┐
│ PluginEditor    │            │ server.py                            │
│   .h / .cpp     │            │  asyncio event loop                  │
│                 │            │  ┌──────────────────────────────┐    │
│ PythonSidecar   │──socket───►│  │ Request dispatcher           │    │
│   .h / .cpp     │            │  │  ping                        │    │
│                 │◄──JSON─── │  │  search { query, filters }   │    │
│ juce::          │            │  │  analyze { path }            │    │
│  ChildProcess   │            │  │  batch_analyze { paths[] }   │    │
│  (lifecycle)    │            │  └──────────────────────────────┘    │
└─────────────────┘            │  ┌──────────────────────────────┐    │
                               │  │ SampleRepository (read-only) │    │
                               │  │ Audio Analyzer (analyze_file)│    │
                               │  └──────────────────────────────┘    │
                               └──────────────────────────────────────┘

Socket:   ~/tmp/samplemind.sock (Unix domain socket)
Protocol: 4-byte big-endian length prefix + UTF-8 JSON body
Lifecycle: plugin editor open → sidecar launch; editor close → sidecar shutdown
Health:   ping every 5s; auto-restart on timeout (max 3 retries)
Version:  {"version": 2, "action": "search", ...} — versioned envelope
```

**Sidecar startup sequence:**

1. `PluginProcessor::prepareToPlay()` → `sidecar.launch(binaryPath)`
2. `juce::ChildProcess::start()` with stdout/stderr captured
3. Wait for ready signal: `{"status": "ready", "version": 2}`
4. Begin health-check ping loop (5 s interval)
5. On editor close: `PluginProcessor::releaseResources()` → `sidecar.shutdown()`

---

## Agent & Tooling Ecosystem

SampleMind uses **19 specialized Claude Code agents** (`.claude/agents/`), **22 Auggie CLI skills**
(`.augment/skills/`), and **13 slash commands** (`.claude/agents/`). Agents auto-activate by
file path, code pattern, or chat keyword — no manual routing needed.

### Domain Agents (always available)

| Agent | Triggers |
|-------|---------|
| `audio-analyzer` | librosa, BPM, WAV, classify, fingerprint, spectral |
| `test-runner` | pytest, tests/, failing, coverage, conftest, fixture |
| `tauri-builder` | Tauri, Rust, Svelte, pnpm tauri, cargo, app/ |
| `api-agent` | FastAPI, /api/v1/, endpoint, Bearer token |
| `web-agent` | Flask, web UI, HTMX, SSE, login page |
| `security-agent` | JWT, RBAC, permission, role, bcrypt |
| `devops-agent` | setup, CI/CD, GitHub Actions, WSL2, install |
| `ml-agent` | ML model, transformers, HuggingFace, embedding |
| `doc-writer` | document, update README, phase doc, ARCHITECTURE |
| `fl-studio-agent` | FL Studio, JUCE, VST3, sidecar, MIDI, AppleScript |

### Phase Agents (activate on "Phase N" mention or matching files)

`phase-02-audio-testing` `phase-03-database` `phase-04-cli` `phase-05-web`
`phase-06-desktop` `phase-07-fl-studio` `phase-08-vst-plugin` `phase-09-sample-packs`
`phase-10-production`

### Slash Commands

```text
/check    /test     /build    /import   /search   /analyze
/serve    /start    /list     /tag      /health   /db-inspect
/auth     /setup    /debug    /pack     /sidecar
```

### Auggie CLI Skills (22 total)

```text
analyze_audio  batch_import  build  check  coverage  db_inspect  db_migrate
fingerprint  health_check  import_samples  lint  list_samples  pack  run_tests
search  serve_api  serve_web  setup_dev  sidecar  start  auth  tag
```

Full routing table with file/code/keyword → agent mapping: `CLAUDE.md` §AI Agent Routing.
Canonical YAML: `.auggie/routing.yaml` and `.auggie/agents.yaml`.
