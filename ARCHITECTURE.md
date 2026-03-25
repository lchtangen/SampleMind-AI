# SampleMind AI — Architecture

> Reference document for the system architecture, data flow, IPC contracts, and technology decisions.

---

## System Layers

```
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
  classify_energy()     → "low" | "medium" | "high"
  classify_mood()       → "dark" | "neutral" | "bright"
  classify_instrument() → "kick" | "snare" | "hihat" | "bass" | ...
     │
     ▼
SampleRepository.upsert()
     │
     ▼
SQLite (SQLModel + SQLAlchemy 2.0)
  samples table: id, filename, path, bpm, key, instrument, mood,
                 energy, duration, tags, created_at, updated_at
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

All communication between Rust (Tauri) and Python uses `stdout` JSON.
Python prints status/progress to `stderr`; JSON data always goes to `stdout`.

| Tauri Command (Rust) | Python CLI Invocation | JSON Response Schema |
|---|---|---|
| `import_folder` | `samplemind import <path> --json` | `{"imported": N, "errors": M, "samples": [...]}` |
| `search_samples` | `samplemind search --query X --json` | `{"samples": [...]}` |
| `analyze_file` | `samplemind analyze <path> --json` | `{"bpm": F, "key": S, "instrument": S, ...}` |
| `get_library_stats` | `samplemind list --stats --json` | `{"total": N, "by_instrument": {...}}` |
| `export_pack` | `samplemind pack create NAME SLUG --json` | `{"pack_path": S, "sample_count": N}` |
| `focus_fl_studio` | `osascript -e 'tell app "FL Studio" to activate'` | *(macOS only, no JSON)* |

### Sample JSON Schema

All commands that return sample data use this schema:

```json
{
  "id": 42,
  "filename": "kick_128bpm.wav",
  "path": "/Users/name/Music/Samples/kick_128bpm.wav",
  "bpm": 128.0,
  "key": "C min",
  "instrument": "kick",
  "mood": "dark",
  "energy": "high",
  "duration": 0.45,
  "tags": ["trap", "808"],
  "created_at": "2025-10-01T12:00:00Z"
}
```

### Python Sidecar Socket Protocol (JUCE Plugin)

Length-prefixed JSON over a Unix domain socket (`~/tmp/samplemind.sock`):

```
Request:  [4-byte big-endian int: length] [UTF-8 JSON bytes]
Response: [4-byte big-endian int: length] [UTF-8 JSON bytes]

Supported actions:
  {"action": "ping"}
  {"action": "search", "query": "...", "energy": "...", "instrument": "..."}
  {"action": "analyze", "path": "/absolute/path/to/file.wav"}
```

---

## Component Responsibilities

| Component | Location | Responsibility |
|---|---|---|
| **Audio Analyzer** | `src/samplemind/analyzer/` | librosa feature extraction and classification |
| **Sample Repository** | `src/samplemind/data/repository.py` | All SQLite read/write via SQLModel |
| **Alembic Migrations** | `alembic/versions/` | Schema changes without data loss |
| **Typer CLI** | `src/samplemind/cli/` | User-facing commands + JSON output for Tauri |
| **Flask Web UI** | `src/samplemind/web/` | Browser-based library management (HTMX) |
| **Svelte Frontend** | `app/src/` | Desktop app UI (reactive, Runes) |
| **Tauri Core** | `app/src-tauri/src/` | Rust commands, system tray, native dialogs |
| **FL Studio Integration** | `src/samplemind/integrations/` | Export, clipboard, AppleScript, MIDI |
| **Pack System** | `src/samplemind/packs/` | .smpack export/import with SHA-256 integrity |
| **Python Sidecar** | `src/samplemind/sidecar/server.py` | Socket server for JUCE plugin communication |
| **JUCE Plugin** | `plugin/src/` | VST3/AU plugin, UI, sidecar lifecycle |

---

## Technology Decision Log

| Technology | Replaces | Rationale |
|---|---|---|
| **uv** | pip + venv | 10–100× faster installs; single tool for packages, virtual envs, and scripts |
| **pyproject.toml** | requirements.txt | PEP 621 standard; one file for deps, scripts, and tool config |
| **src-layout** | flat layout | Prevents accidental imports of the source tree instead of the installed package |
| **SQLModel** | raw sqlite3 | Type-safe ORM backed by Pydantic + SQLAlchemy 2.0; less boilerplate |
| **Alembic** | `_migrate()` function | Proper migration history; reversible; works in CI |
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
│   ├── __init__.py              ← __version__
│   ├── __main__.py              ← python -m samplemind
│   ├── models.py                ← SQLModel Sample class
│   ├── cli/
│   │   ├── app.py               ← Typer main app
│   │   └── commands/            ← import_, search, tag, serve, export, pack
│   ├── analyzer/
│   │   ├── audio_analysis.py    ← librosa feature extraction
│   │   └── classifier.py        ← energy/mood/instrument classification
│   ├── data/
│   │   ├── db.py                ← engine setup, platformdirs path
│   │   └── repository.py        ← SampleRepository class
│   ├── web/
│   │   ├── app.py               ← Flask create_app() factory
│   │   ├── blueprints/          ← library, import (SSE)
│   │   ├── templates/           ← Jinja2 + HTMX partials
│   │   └── static/              ← CSS, wavesurfer.js
│   ├── integrations/
│   │   ├── paths.py             ← FL Studio path detection
│   │   ├── filesystem.py        ← export_to_fl_studio()
│   │   ├── clipboard.py         ← copy_sample_path()
│   │   ├── applescript.py       ← macOS automation
│   │   ├── midi.py              ← python-rtmidi CC messages
│   │   └── naming.py            ← FL Studio filename conventions
│   ├── packs/
│   │   ├── manifest.py          ← PackManifest Pydantic model
│   │   ├── exporter.py          ← export_pack()
│   │   └── importer.py          ← import_pack()
│   └── sidecar/
│       └── server.py            ← Unix socket server (for JUCE plugin)
├── app/                         ← Tauri desktop application
│   ├── src/                     ← Svelte 5 frontend
│   │   └── lib/
│   │       ├── components/      ← SampleTable, ImportPanel, WaveformPlayer
│   │       ├── stores/          ← library.svelte.ts ($state)
│   │       └── api/             ← tauri.ts (typed invoke() wrappers)
│   ├── src-tauri/
│   │   ├── src/
│   │   │   ├── main.rs          ← app entry, tray, setup
│   │   │   └── commands/        ← import, search, applescript
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   ├── entitlements.plist   ← macOS sandbox entitlements
│   │   └── resources/           ← samplemind-sidecar binary (PyInstaller)
│   ├── package.json
│   └── vite.config.ts
├── plugin/                      ← JUCE VST3/AU plugin (C++)
│   ├── CMakeLists.txt
│   └── src/
│       ├── PluginProcessor.h/.cpp
│       ├── PluginEditor.h/.cpp
│       ├── PythonSidecar.h/.cpp
│       └── IPCSocket.h/.cpp
├── alembic/                     ← Database migrations
│   ├── alembic.ini
│   └── versions/
│       └── 0001_initial.py
├── tests/                       ← pytest test suite
│   ├── conftest.py              ← WAV fixtures, DB fixtures
│   ├── test_audio_analysis.py
│   ├── test_classifier.py
│   ├── test_repository.py
│   ├── test_cli.py
│   ├── test_web.py
│   └── test_packs.py
├── docs/
│   ├── no/                      ← Norwegian phase docs
│   └── en/                      ← English phase docs
├── scripts/
│   ├── setup-dev.sh             ← Bootstrap for new contributors
│   ├── bump-version.sh          ← Sync version across 4 files
│   ├── build-sidecar.sh         ← PyInstaller build
│   └── release-pack.sh          ← GitHub Release for .smpack
├── .github/workflows/
│   ├── ci.yml                   ← pytest + ruff + clippy
│   └── release.yml              ← macOS sign + notarize + Windows build
├── pyproject.toml               ← Python package config (uv)
├── samplemind-sidecar.spec      ← PyInstaller spec
├── ARCHITECTURE.md              ← This file
├── ROADMAP.md
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

**Current bottlenecks (Phase 1 state):**
- Single file: ~800ms (librosa cold import overhead)
- Batch: sequential (no workers yet — Phase 2 task)
- Search: full table scan (no FTS5 yet — Phase 3 task)

---

## Security Model

- **No network access required** — SampleMind is a fully local application
- **macOS sandbox entitlements:** minimum required set only (no broad disk access)
- **No credentials stored** — SQLite database is a plain user-owned file
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

