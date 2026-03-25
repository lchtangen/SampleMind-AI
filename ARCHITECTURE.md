# SampleMind AI — Architecture

> Reference document for the system architecture, data flow, IPC contracts, and technology decisions.

---

## System Layers

 
```text
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4 — DAW Integration                                      │
│  ┌─────────────────────┐   ┌──────────────────────────────────┐ │
│  │  JUCE Plugin (C++)  │   │  FL Studio (macOS/Windows)       │ │
│  │  VST3 + AU          │   │  - Filesystem browser            │ │
│  │  PluginEditor UI    │   │  - AppleScript automation        │ │
│  │  PythonSidecar      │   │  - Virtual MIDI (IAC Driver)     │ │
│  └──────────┬──────────┘   └──────────────────────────────────┘ │
└─────────────┼───────────────────────────────────────────────────┘
              │ Unix domain socket (~/tmp/samplemind.sock)
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 3 — Desktop Application (Tauri 2)                        │
│  ┌──────────┴──────────┐                                        │
│  │  Svelte 5 + Vite     │  UI: SampleTable, ImportPanel,        │
│  │  (WKWebView on macOS)│       WaveformPlayer, SearchBar       │
│  └──────────┬──────────┘                                        │
│             │ tauri::invoke() IPC                               │
│  ┌──────────┴──────────┐                                        │
│  │  Rust (Tauri core)  │  Commands: import_folder,              │
│  │  app/src-tauri/     │            search_samples,             │
│  │                     │            pick_folder_dialog,         │
│  │                     │            focus_fl_studio             │
│  └──────────┬──────────┘                                        │
└─────────────┼───────────────────────────────────────────────────┘
              │ stdout JSON (samplemind import --json ...)
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 2 — Python Backend                                       │
│  ┌──────────┴──────────┐                                        │
│  │  Typer CLI          │  Commands: import, analyze, search,    │
│  │  src/samplemind/    │            tag, serve, export, pack    │
│  │  cli/app.py         │                                        │
│  └──────────┬──────────┘                                        │
│             │                                                   │
│  ┌──────────┴──────────────────────────────────┐                │
│  │  Core Services                               │               │
│  │  ┌────────────────┐  ┌────────────────────┐ │                │
│  │  │ Audio Analysis │  │ Sample Repository  │ │                │
│  │  │ librosa 0.11   │  │ SQLModel + Alembic │ │                │
│  │  │ 8 features     │  │ SQLite database    │ │                │
│  │  └────────────────┘  └────────────────────┘ │                │
│  │  ┌────────────────┐  ┌────────────────────┐ │                │
│  │  │ Flask Web UI   │  │ Pack System        │ │                │
│  │  │ HTMX + SSE     │  │ .smpack ZIP format │ │                │
│  │  └────────────────┘  └────────────────────┘ │                │
│  └─────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼───────────────────────────────────────────────────┐
│  Layer 1 — Storage                                              │
│  ┌──────────┴──────────┐   ┌──────────────────────────────────┐ │
│  │  SQLite DB          │   │  Audio Files                     │ │
│  │  ~/Library/         │   │  ~/Music/SampleMind/             │ │
│  │  Application        │   │  (WAV, original paths preserved) │ │
│  │  Support/SampleMind │   │                                  │ │
│  └─────────────────────┘   └──────────────────────────────────┘ │

└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

 
```
WAV file on disk
     │
     ▼
librosa.load()          ← scipy FFT backend, soxr_hq resampling
     │
     ▼
Feature extraction (8 features per file)
  rms                   ← energy amplitude
  spectral_centroid     ← brightness (normalized to Nyquist)
  zero_crossing_rate    ← texture (hihats ≈ 0.35, kicks ≈ 0.03)
  spectral_flatness     ← noise vs. tone (0=sine, 1=white noise)
  spectral_rolloff      ← 85% energy frequency (normalized)
  onset_mean/max        ← rhythmic attack strength
  low_freq_ratio        ← bass presence below 300 Hz
  duration              ← file length in seconds
     │
     ▼
Classification (3 independent classifiers)
  classify_energy()     → "low" | "mid" | "high"
  classify_mood()       → "dark" | "chill" | "aggressive" | "euphoric" | "melancholic" | "neutral"
  classify_instrument() → "kick" | "snare" | "hihat" | "bass" | "pad" | "lead" | "loop" | "sfx" | "unknown"
     │
     ▼
SampleRepository.upsert()  ← data/repositories/sample_repository.py (SQLModel)
     │                            Auto-detected fields only; user tags are never
     │                            overwritten on re-import (genre, tags preserved)
     ▼
SQLite (platformdirs path: ~/Library/Application Support/SampleMind/samplemind.db)
  users table:   id, email, role, hashed_password, is_active, created_at
  samples table: id, filename, path, bpm, key, mood, genre,
                 energy, tags, instrument, imported_at
  WAL mode + performance PRAGMAs applied on every connection via SQLAlchemy event
     │
     ├──► Typer CLI (stdout JSON for Tauri IPC)
     ├──► Flask Web UI (HTMX partials, SSE progress)
     ├──► Tauri Desktop App (invoke() commands)
     ├──► FL Studio export (filesystem, clipboard, MIDI)
     ├──► JUCE Plugin (via Python sidecar socket)
    └──► .smpack pack export/import
  ```

---

## IPC Contract Table

### Current State (Phase 1–4 runtime)

The Tauri app currently loads the Flask web UI in a WebView at `http://127.0.0.1:5174`.
Rust commands handle OS-level tasks and auth token storage; Python logic runs over HTTP
(not direct subprocess calls yet — that comes with the Svelte frontend in Phase 7).

| Tauri Command (Rust) | Purpose | Return type |
|---|---|---|
| `pick_folder` | Native folder picker dialog (tauri-plugin-dialog) | `Option<String>` (path or null) |
| `is_directory` | Check if a path is a directory on disk | `bool` |
| `store_token` | Store a JWT access token in `AuthTokenStore` (Mutex-protected) | `()` |
| `get_token` | Retrieve the stored token, if any | `Option<String>` |
| `clear_token` | Clear the stored token (logout) | `()` |

Flask serves the library UI at port 5174 (Tauri-spawned) or 5000 (standalone `samplemind serve`).

### Target State (Phase 6+ — Svelte frontend replaces WebView)

Once the Svelte 5 frontend is built, Tauri will call Python via subprocess stdout JSON:

| Tauri Command (Rust) | Python CLI Invocation | JSON Response Schema |
|---|---|---|
| `import_folder` | `samplemind import <path> --json` | `{"imported": N, "errors": M}` |
| `search_samples` | `samplemind search <query> --json` | `[{"filename": S, "bpm": F, ...}]` |
| `analyze_file` | `samplemind analyze <path> --json` | `{"bpm": F, "key": S, "energy": S, "mood": S, "instrument": S}` |
| `get_stats` | `samplemind list --json` | `[{"filename": S, ...}]` |

### `analyze_file` JSON Output (actual — Phase 1 runtime)

`samplemind analyze <path> --json` returns exactly these 5 fields:

 
```json
{
  "bpm": 128.0,
  "key": "C min",
  "energy": "mid",
  "mood": "dark",
  "instrument": "kick"
}
```

### Database Row Schema (actual — `~/.samplemind/library.db`)

 
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

> **Note:** `energy` values are `low` / `mid` / `high`. Tags are stored as a comma-separated string, not a JSON array. There is no `duration` field in the current schema.

### Python Sidecar Socket Protocol (JUCE Plugin)

Length-prefixed JSON over a Unix domain socket (`~/tmp/samplemind.sock`):

 
```text
Request:  [4-byte big-endian int: length] [UTF-8 JSON bytes]
Response: [4-byte big-endian int: length] [UTF-8 JSON bytes]

Supported actions:
  {"action": "ping"}
  {"action": "search", "query": "...", "energy": "...", "instrument": "..."}
  {"action": "analyze", "path": "/absolute/path/to/file.wav"}
```

---

## Component Responsibilities

| Component | Location | Status | Responsibility |
|---|---|---|---|
| **Audio Analyzer** | `src/samplemind/analyzer/audio_analysis.py` | ✅ Live | librosa BPM + key detection; 8 feature vectors |
| **Classifier** | `src/samplemind/analyzer/classifier.py` | ✅ Live | Rule-based energy (low/mid/high), mood (dark/chill/aggressive/euphoric/melancholic/neutral), instrument (kick/snare/hihat/bass/pad/lead/loop/sfx/unknown) |
| **SQLModel ORM** | `src/samplemind/data/orm.py` | ✅ Live | Shared engine; WAL + PRAGMAs via SQLAlchemy event; `get_session()` context manager |
| **SampleRepository** | `src/samplemind/data/repositories/sample_repository.py` | ✅ Live | All sample CRUD (upsert, search, tag, get_by_name/path/id, count, get_all) |
| **UserRepository** | `src/samplemind/data/repositories/user_repository.py` | ✅ Live | User CRUD (create, get_by_email, get_by_id) |
| **Auth (JWT + RBAC)** | `src/samplemind/core/auth/` | ✅ Live | JWT access + refresh tokens; bcrypt hashing; viewer/owner/admin RBAC |
| **FastAPI routes** | `src/samplemind/api/routes/auth.py` | ✅ Live | /register /login /refresh /me /change-password |
| **Typer CLI** | `src/samplemind/cli/` | ✅ Live | 8 commands: version, import, analyze, list, search, tag, serve, api; `--json` on all |
| **Flask Web UI** | `src/samplemind/web/app.py` | ✅ Live | 10+ routes; library view, search, tag, audio streaming, auth-gated pages |
| **Tauri Core** | `app/src-tauri/src/main.rs` | ✅ Live | 5 Rust commands: pick_folder, is_directory, store_token, get_token, clear_token; system tray |
| **Svelte Frontend** | `app/src/` | 📋 Phase 7 | Not built yet — Tauri currently loads Flask WebView at port 5174 |
| **FL Studio Integration** | `src/samplemind/integrations/` | 📋 Phase 8 | Planned: filesystem export, AppleScript, MIDI |
| **Pack System** | `src/samplemind/packs/` | 📋 Phase 10 | Planned: .smpack ZIP format with SHA-256 integrity |
| **Python Sidecar** | `src/samplemind/sidecar/` | 📋 Phase 9 | Planned: Unix socket server for JUCE plugin IPC |
| **JUCE Plugin** | `plugin/src/` | 📋 Phase 9 | Planned: VST3/AU plugin for FL Studio |

---

## Technology Decision Log

| Technology | Replaces | Rationale |
| --- | --- | --- |
| **uv** | pip + venv | 10–100× faster installs; single tool for packages, virtual envs, and scripts |
| **pyproject.toml** | requirements.txt | PEP 621 standard; one file for deps, scripts, and tool config |
| **src-layout** | flat layout | Prevents accidental imports of the source tree instead of the installed package |
| **SQLModel** | raw sqlite3 | Type-safe ORM: SQLAlchemy 2.0 + Pydantic v2 in one class; `Sample` and `User` tables live |
| **Alembic** | `_migrate()` function | Versioned, reversible schema migrations; `migrations/versions/0001` (users) + `0002` (samples) applied |
| **bcrypt (direct)** | passlib[bcrypt] | passlib 1.7.x cannot parse bcrypt 4.x/5.x version strings; use `bcrypt` package directly |
| **FastAPI** | Flask (for API) | Async request handling; auto OpenAPI docs at `/docs`; Pydantic v2 native validation |
| **python-jose** | PyJWT | Supports both HS256 and RS256; used for JWT access + refresh tokens |
| **StaticPool** in tests | thread-local pools | Keeps in-memory SQLite on one connection across all threads — required for FastAPI test client |
| **expire_on_commit=False** | default Session | Prevents `DetachedInstanceError` when accessing fields on ORM objects returned from `get_session()` |
| **Typer + Rich** | argparse | Type annotations = automatic `--help` and validation; Rich = beautiful terminal output |
| **HTMX** | custom JS fetch | Replaces 80% of hand-written JavaScript with HTML attributes; simpler to maintain |
| **SSE (Server-Sent Events)** | polling | One-way streaming from server to browser; no WebSocket overhead |
| **Tauri 2** | Electron | 3–15 MB bundle vs 120–200 MB; Rust backend; uses system WebView (WKWebView on macOS) |
| **Svelte 5 Runes** | Svelte 4 stores | Fine-grained reactivity; no hidden implicit dependencies; `.svelte.ts` stores |
| **JUCE 8** | — | Industry standard for audio plugins; VST3 + AU from one codebase |
| **Unix domain socket** | TCP socket | Lower latency for local IPC; no port conflict risk |
| **PyInstaller** | requiring Python | Bundles the sidecar as a standalone binary for end-user distribution |
| **GitHub Actions** | manual builds | Reproducible CI/CD; macOS signing + notarization automated |
| **pytest + soundfile fixtures** | none | Synthetic WAV generation for reproducible audio tests without real sample files |

---

## Development vs Production Topology

### Development (Windows WSL2)

 
```
Windows 11
└── WSL2 (Ubuntu 24.04)
    ├── /home/ubuntu/dev/projects/SampleMind-AI/  ← all code here (Linux ext4, fast)
    │   ├── uv run samplemind ...                  ← Python CLI
    │   ├── uv run pytest ...                      ← tests
    │   └── cargo clippy ...                       ← Rust linting
    └── VS Code WSL extension connects here

NOTE: Do NOT store code under /mnt/c/ (NTFS is 5–10× slower for git/Python)
```

### Production (macOS)

 
```
macOS 12+ (Apple Silicon preferred)
└── SampleMind.app  (Tauri bundle, ~15 MB)
    ├── Contents/
    │   ├── MacOS/
    │   │   ├── SampleMind              ← Tauri/Rust binary
    │   │   └── samplemind-sidecar      ← PyInstaller bundle
    │   ├── Resources/
    │   │   └── (Svelte/Vite build)
    │   └── Info.plist
    └── (signed with Developer ID + notarized by Apple)

FL Studio plugins:
    ~/Library/Audio/Plug-Ins/Components/SampleMind.component  ← AU
    ~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3             ← VST3

Sample library:
    ~/Music/SampleMind/    ← organized by instrument/mood
    ~/Library/Application Support/SampleMind/samplemind.db  ← SQLite
  ```

---

## Repository Structure

 
```
SampleMind-AI/
├── src/samplemind/              ← Python package (src-layout)
│   ├── __init__.py              ← __version__ = "0.2.0"
│   ├── __main__.py              ← python -m samplemind entry point
│   ├── cli/
│   │   ├── app.py               ← Typer main app; registers all 8 commands
│   │   └── commands/
│   │       ├── import_.py       ← samplemind import <folder> [--json]
│   │       ├── analyze.py       ← samplemind analyze <file> [--json]
│   │       ├── library.py       ← samplemind list / search [filters] [--json]
│   │       ├── tag.py           ← samplemind tag <name> [--genre] [--mood] ...
│   │       └── serve.py         ← samplemind serve / api
│   ├── analyzer/
│   │   ├── audio_analysis.py    ← librosa feature extraction: analyze_file()
│   │   └── classifier.py        ← rule-based classifiers (energy/mood/instrument)
│   ├── core/
│   │   ├── config.py            ← Settings (pydantic-settings, env vars, platformdirs)
│   │   ├── auth/
│   │   │   ├── jwt_handler.py   ← create_access_token(), create_refresh_token(), decode_token()
│   │   │   ├── password.py      ← hash_password(), verify_password() via bcrypt
│   │   │   ├── rbac.py          ← UserRole enum, Permission enum, ROLE_PERMISSIONS map
│   │   │   └── dependencies.py  ← FastAPI Depends helpers: get_current_user(), require_role()
│   │   └── models/
│   │       ├── user.py          ← User SQLModel table + UserCreate/UserUpdate/UserPublic
│   │       └── sample.py        ← Sample SQLModel table + SampleCreate/SampleUpdate/SamplePublic
│   ├── data/
│   │   ├── orm.py               ← get_engine(), init_orm(), get_session() context manager; WAL PRAGMAs
│   │   ├── database.py          ← legacy sqlite3 functions (superseded by orm.py — kept for reference)
│   │   └── repositories/
│   │       ├── user_repository.py    ← UserRepository (create, get_by_email, get_by_id)
│   │       └── sample_repository.py  ← SampleRepository (upsert, search, tag, get_by_*, count, get_all)
│   ├── api/
│   │   ├── main.py              ← FastAPI app factory
│   │   └── routes/
│   │       └── auth.py          ← /register /login /refresh /me /change-password
│   └── web/
│       ├── app.py               ← Flask app; library view, search, tag, audio streaming, auth
│       ├── templates/           ← Jinja2 templates (index.html, login.html, register.html)
│       └── static/              ← CSS, JS
├── app/                         ← Tauri desktop application
│   ├── src-tauri/
│   │   ├── src/
│   │   │   └── main.rs          ← app entry; 5 Rust commands; system tray; AuthTokenStore
│   │   ├── Cargo.toml           ← tauri 2.x, tauri-plugin-dialog, serde_json
│   │   ├── tauri.conf.json      ← bundle targets: dmg, msi, appimage
│   │   └── entitlements.plist   ← macOS sandbox entitlements (outgoing-network, etc.)
│   └── package.json             ← pnpm workspace; @tauri-apps/cli, @tauri-apps/api
├── migrations/                  ← Alembic schema history
│   ├── env.py                   ← async-aware env; render_as_batch=True for SQLite
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_create_users_table.py   ← users schema baseline
│       └── 0002_create_samples_table.py ← samples schema (+ ix_samples_filename index)
├── tests/                       ← pytest test suite (33 tests)
│   ├── conftest.py              ← WAV fixtures (silent/kick/hihat), orm_engine, test_user, access_token
│   ├── test_audio_analysis.py   ← BPM, key, feature extraction tests
│   ├── test_classifier.py       ← energy, mood, instrument classifier tests
│   ├── test_auth.py             ← 24 tests: JWT, bcrypt, RBAC, FastAPI auth routes
│   ├── test_cli.py              ← Typer CliRunner tests
│   └── test_web.py              ← Flask test client tests
├── docs/
│   ├── FIRST_SAMPLEMIND_PROJECT_ROADMAP.md  ← master engineering + product vision
│   ├── no/                      ← Norwegian phase docs
│   └── en/                      ← English phase docs (phase-01 through phase-06)
├── scripts/
│   ├── setup-dev.sh             ← bootstrap for new contributors
│   ├── bump-version.sh          ← sync version across pyproject.toml + Cargo.toml
│   ├── build-sidecar.sh         ← PyInstaller build (Phase 11)
│   └── release-pack.sh          ← GitHub Release for .smpack (Phase 10)
├── .github/workflows/
│   ├── python-lint.yml          ← ruff + pyright + pytest + alembic check
│   └── release.yml              ← macOS sign + notarize + Windows build (Phase 11)
├── pyproject.toml               ← Python package config (uv); version 0.2.0
├── alembic.ini                  ← points to migrations/ and samplemind.db
├── samplemind-sidecar.spec      ← PyInstaller spec (Phase 11)
├── ARCHITECTURE.md              ← this file
├── ROADMAP.md                   ← all 13+ phases
└── README.md
```

---

## ML Pipeline

Feature extraction → Classification pipeline details:

- **Batch processing:** concurrent analysis with configurable `--workers` (default: CPU count via `os.cpu_count()`)
- **Fingerprinting:** SHA-256 of first 64KB for deduplication detection before analysis
- **Analysis cache:** skip re-analysis if file `mtime` is unchanged (planned Phase 2 optimization)
- **Model targets:** audio fingerprint similarity search for "find similar sounds" feature (Phase 2+)
- **ProcessPoolExecutor:** used for batch imports — each worker runs `analyze_file()` independently

 
```
Batch import flow:
files[]
  │
  ├── fingerprint_file() ─────► deduplicate check (skip known files)
  │
  └── ProcessPoolExecutor(workers=N)
        │
        └── analyze_file(path)
              ├── librosa.load()
              ├── extract 8 features
              ├── classify_energy/mood/instrument()
              └── SampleRepository.upsert()
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Single file analysis | < 500ms | librosa on 22050 Hz mono WAV |
| Batch import (100 files) | < 30s | parallel workers, 8-core machine |
| Search query | < 50ms | SQLite FTS5 full-text index |
| Tauri cold start | < 2s | macOS, sidecar excluded |
| Sidecar startup | < 3s | PyInstaller one-file bundle |
| VST3 UI open | < 200ms | JUCE editor open, cached socket |

**Current bottlenecks (Phase 4 state — v0.2.0):**
- Single file: ~800ms (librosa cold-import overhead on first call; subsequent calls are faster)
- Batch: sequential (no workers yet — `--workers N` planned for Phase 5)
- Search: full table scan via SQLModel `WHERE ... LIKE` (FTS5 virtual table planned for Phase 5)
- Analysis results are not yet cached by `mtime`/`size`; every re-import re-runs librosa

---

## Security Model

- **No mandatory network access** — all analysis, storage, and search run locally; cloud APIs are opt-in
- **macOS sandbox entitlements:** minimum required set only in `app/src-tauri/entitlements.plist` (outgoing-network for optional API calls, no broad disk access)
- **Credentials:** JWT tokens (access + refresh) stored in `AuthTokenStore` (Mutex-protected, in-memory only) in the Rust Tauri process; never written to disk; cleared on `clear_token` IPC call
- **Passwords:** bcrypt-hashed (cost factor 12+) before storage; plaintext never persisted or logged
- **SQLite:** plain user-owned file; no encryption (user's own sample library data, not PII); protected by OS file permissions
- **Sidecar binary:** PyInstaller one-file bundle; SHA-256 checksum verified at Tauri startup before execution
- **Code signing:**
  - macOS: Apple Developer ID Application certificate + notarization via `xcrun notarytool`
  - Windows: Azure Trusted Signing (replaces EV certificate requirement)
- **Audio files:** never copied or modified unless user explicitly triggers an export action
- **No telemetry by default:** Sentry integration is opt-in via `SAMPLEMIND_SENTRY_DSN` env var
- **Database:** no encryption (user data, not sensitive) — file permissions protect it

---

## Observability

- **Structured logging:** Python `logging` module → `stderr` only (never `stdout`, preserves IPC contract)
- **Log levels:**
  - `DEBUG` — analysis feature values, import timing, socket messages
  - `INFO` — import counts, search results, server startup
  - `WARNING` — missing optional dependencies (soxr, rtmidi), degraded mode
  - `ERROR` — analysis failures, DB write errors, sidecar crashes
- **Sentry (opt-in, Phase 10):** crash reporting with `traces_sample_rate=0.1`, no PII captured
- **Performance metrics:** import time and analysis time logged at `DEBUG` level per file
- **CLI `--verbose` flag:** enables `DEBUG` logging for troubleshooting
- **Tauri:** `tauri::api::log` for Rust-side events; forwarded to system console

 
```python
# Correct logging pattern — stderr only:
import logging
logger = logging.getLogger(__name__)
logger.debug("analyze: path=%s duration_ms=%d", path, elapsed_ms)
# NEVER: print(json_result) to stderr — breaks IPC
# NEVER: logger.info(json.dumps(result)) — JSON to stderr confuses parsers
```

---

## Sidecar v2 Architecture (Phase 8+)

 
```
JUCE Plugin                    Python Sidecar (PyInstaller bundle)
┌─────────────────┐            ┌──────────────────────────────────────┐
│ PluginEditor    │            │ server.py                            │
│   .h/.cpp       │            │  asyncio event loop                  │
│                 │            │  ┌──────────────────────────────┐    │
│ PythonSidecar   │──socket───►│  │ Request dispatcher           │    │
│   .h/.cpp       │            │  │  ping                        │    │
│                 │◄──JSON────│  │  search { query, filters }   │    │
│ juce::          │            │  │  analyze { path }            │    │
│  ChildProcess   │            │  │  batch_analyze { paths[] }   │    │
│  (lifecycle)    │            │  └──────────────────────────────┘    │
└─────────────────┘            │  ┌──────────────────────────────┐    │
                               │  │ SampleRepository (read-only) │    │
                               │  │ Audio Analyzer               │    │
                               │  └──────────────────────────────┘    │
                               └──────────────────────────────────────┘

Socket:   ~/tmp/samplemind.sock (Unix domain socket)
Protocol: 4-byte big-endian length prefix + UTF-8 JSON body
Lifecycle: plugin launches sidecar on editor open, kills on editor close
Health:   ping every 5s, auto-restart on timeout (max 3 retries)
Version:  {"version": 2, "action": "search", ...} — versioned envelope
```

**Sidecar startup sequence:**
1. `PluginProcessor::prepareToPlay()` → `sidecar.launch(binaryPath)`
2. `juce::ChildProcess::start()` with stdout/stderr captured
3. Wait for "ready" JSON on stdout: `{"status": "ready", "version": 2}`
4. Begin health-check ping loop (5s interval)
5. On editor close: `PluginProcessor::releaseResources()` → `sidecar.shutdown()`

