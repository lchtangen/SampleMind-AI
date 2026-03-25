# SampleMind AI — Roadmap & Technical Guide

> **Main goal:** Build an AI-powered sample library and DAW companion for FL Studio on macOS (and Windows). The tool should analyze, tag, organize, and export samples — and ultimately integrate directly with FL Studio via native macOS mechanisms or plugin APIs.

---

## Table of Contents

1. [Project Overview and Architecture](#1-project-overview-and-architecture)
2. [Tech Stack — What We Use and Why](#2-tech-stack--what-we-use-and-why)
3. [Tauri vs Electron — Desktop UI Choice](#3-tauri-vs-electron--desktop-ui-choice)
4. [FL Studio Integration — macOS and Windows](#4-fl-studio-integration--macos-and-windows)
5. [Phase 1 — Foundation & CLI ✅](#5-phase-1--foundation--cli-)
6. [Phase 2 — Audio Testing & Analysis ✅](#6-phase-2--audio-testing--analysis-)
7. [Phase 3 — Authentication & Authorization ✅](#7-phase-3--authentication--authorization-)
8. [Phase 4 — Database & Data Layer ✅](#8-phase-4--database--data-layer-)
9. [Phase 5 — CLI Modernization 📋](#9-phase-5--cli-modernization-)
10. [Phase 6 — Web UI Improvements 📋](#10-phase-6--web-ui-improvements-)
11. [Phase 7 — Desktop App (Tauri + Svelte 5) 📋](#11-phase-7--desktop-app-tauri--svelte-5-)
12. [Phase 8 — FL Studio Automation 📋](#12-phase-8--fl-studio-automation-)
13. [Phase 9 — VST3/AU Plugin 📋](#13-phase-9--vst3au-plugin-)
14. [Phase 10 — Sample Packs 📋](#14-phase-10--sample-packs-)
15. [Phase 11 — Production & Release 📋](#15-phase-11--production--release-)
16. [Phase 12 — Semantic Search & Vector Embeddings 📋](#16-phase-12--semantic-search--vector-embeddings-)
17. [Phase 13 — AI Agent Automation 📋](#17-phase-13--ai-agent-automation-)
18. [Backlog and Future Ideas](#18-backlog-and-future-ideas)
19. [Long-term Vision 2026–2030](#19-long-term-vision-20262030)
20. [Technology Decision Log](#20-technology-decision-log)

---

## 1. Project Overview and Architecture

```
SampleMind-AI/
├── src/
│   ├── main.py                     # Legacy entry point (required by Tauri dev mode)
│   ├── samplemind/                 # New src-layout package (Python 3.13)
│   │   ├── __init__.py
│   │   ├── analyzer/
│   │   │   ├── audio_analysis.py   # librosa: BPM, key, energy, mood, instrument
│   │   │   └── classifier.py       # Rule-based: 9 features → energy/mood/instrument
│   │   ├── cli/
│   │   │   ├── app.py              # Typer CLI: import/analyze/list/search/tag/serve
│   │   │   └── commands/           # One module per command
│   │   ├── data/
│   │   │   └── database.py         # sqlite3: ~/.samplemind/library.db
│   │   └── web/
│   │       └── app.py              # Flask web UI (localhost:5000)
├── app/                            # Tauri 2 desktop app
│   ├── src-tauri/
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   └── src/main.rs             # Rust: pick_folder, is_directory commands
│   ├── src/                        # Svelte 5 frontend
│   └── package.json                # pnpm scripts
├── plugin/                         # JUCE 8 VST3/AU plugin (Phase 8, planned)
├── scripts/
│   ├── setup-dev.sh                # Dev environment setup
│   └── start.sh                    # Quick-start services
├── tests/                          # pytest suite (soundfile fixtures, no real audio)
├── docs/en/                        # English phase docs (phase-01 through phase-10)
├── docs/no/                        # Norwegian phase docs
├── pyproject.toml                  # uv + ruff + pytest config (replaces requirements.txt)
└── .github/workflows/ci.yml        # CI: uv+ruff+pytest+clippy
```

### Data Flow (current)

```
WAV file → librosa load → BPM + Key + Chroma →
  classifier.py (rule-based AI) → energy + mood + instrument →
    SQLite database → CLI / Web UI / Tauri UI
```

### Data Flow (future target)

```
FL Studio drag-and-drop / sample browser →
  SampleMind Tauri App (native macOS/Windows) →
    Python backend over IPC →
      AI analysis (librosa + transformers) →
        Database + tags + metadata →
          Back to FL Studio browser via AppleScript / COM / plugin API
```

---

## 2. Tech Stack — What We Use and Why

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Runtime** | Python | 3.13 (GIL + JIT preview) | 3.13 ships experimental JIT (`--jit`); 3.14 brings free-threaded mode (PEP 703) for true parallel audio processing |
| **Packaging** | uv (Astral) | ≥0.6 | 10–100× faster than pip; single tool for venv, add, run, publish, workspace |
| **Audio analysis** | librosa | 0.11.x | Industry standard; BPM, key, spectral features, onset detection |
| **Beat tracking** | madmom (Python ≤3.11) | 0.16.1 | RNN downbeat + beat tracker from CPJKU; best-in-class accuracy; requires separate conda env |
| **AI audio embeddings** | CLAP (HuggingFace ClapModel) | transformers ≥4.40 | Contrastive Language-Audio Pretraining; zero-shot audio classification via text query |
| **Vector search** | **sqlite-vec** | ≥0.1.7 | Pure-C SQLite extension; float32/int8/binary vectors; sub-millisecond ANN search; zero extra infra |
| **AI agents** | **pydantic-ai** | ≥1.0 | Model-agnostic (Claude/GPT/Gemini/Ollama); type-safe tools via Python type annotations; structured outputs |
| **Semantic text search** | sentence-transformers | ≥3.0 | Encode tag text and user queries into embeddings for "find similar" queries |
| **ML classifier** | scikit-learn | ≥1.6 | RandomForest/KNN — upgrade path from rule-based to trained classifier |
| **Database ORM** | SQLModel + Alembic | ≥0.0.21 / ≥1.14 | Type-safe ORM (SQLAlchemy 2 + Pydantic v2); Alembic for versioned migrations |
| **API** | FastAPI + Uvicorn | ≥0.115 / ≥0.34 | Async, auto OpenAPI docs, Pydantic v2 validation |
| **Auth** | python-jose + bcrypt | ≥3.3 / ≥4.x | JWT HS256/RS256; direct bcrypt (passlib incompatible with bcrypt 4.x/5.x) |
| **Web UI (local)** | Flask + HTMX + SSE | ≥3.1 | Simple local server; HTMX for reactivity; SSE for import progress stream |
| **CLI** | Typer + Rich | ≥0.12 / ≥13 | Type-safe commands; auto `--help`; Rich tables + progress bars |
| **Desktop app** | Tauri 2 + Svelte 5 Runes | ≥2.1 / ≥5.0 | 3–15 MB bundle vs 120–200 MB Electron; Svelte 5 Runes = fine-grained reactivity |
| **Linting/format** | Ruff | ≥0.15 | Replaces flake8 + isort + black in one Rust binary; <100ms on full repo |
| **Type checking** | Pyright | ≥1.1.390 | Rust-based; faster than mypy; first-class Pydantic v2 support; VSCode default |
| **Testing** | pytest + hypothesis | ≥9 / ≥6 | Hypothesis: property-based / fuzz testing to find edge cases automatically |
| **Observability** | Logfire (Pydantic) | ≥3.0 | OpenTelemetry-native; auto-instruments FastAPI, SQLModel, httpx, pydantic-ai |
| **Logging** | structlog | ≥24.4 | Structured JSON logs → Logfire / console; never pollutes stdout (IPC contract) |
| **Plugin (Phase 9)** | JUCE 8 (C++) | ≥8.0 | VST3 + AU from one codebase; Python sidecar via Unix socket |
| **Local LLM (future)** | Ollama | — | Run Llama 3, Gemma 3, Qwen 2.5 locally; pydantic-ai `OllamaModel` provider |

---

## 3. Tauri vs Electron — Desktop UI Choice

### What is Tauri?

Tauri is a **Rust-based framework** for building desktop apps with a web frontend. Instead of bundling an entire Chromium browser (as Electron does), Tauri uses the operating system's **built-in WebView**:

- **macOS** → `WKWebView` (Safari engine)
- **Windows** → `WebView2` (Edge Chromium-based)
- **Linux** → `WebKitGTK`

```
┌─────────────────────────────────────────┐
│  Electron                               │
│  ┌─────────────────────────────────┐   │
│  │  Chromium (100MB+)              │   │  ← Entire browser bundled
│  │  + Node.js                      │   │
│  │  + Your app code                │   │
│  └─────────────────────────────────┘   │
│  App size: ~120-200MB                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Tauri                                  │
│  ┌───────────────┐ ┌─────────────────┐ │
│  │  Rust backend │ │  OS WebView     │ │  ← Uses system browser
│  │  (your logic) │ │  (WKWebView)    │ │
│  └───────────────┘ └─────────────────┘ │
│  App size: ~3-15MB                      │
└─────────────────────────────────────────┘
```

### Comparison

| Property | Tauri | Electron |
|----------|-------|----------|
| App size | ~3–15 MB | ~120–200 MB |
| RAM usage | Low (Rust backend) | High (Node + Chromium) |
| Performance | Very fast | Slower |
| macOS native API | Direct from Rust | Via Node native modules |
| Learning curve | Higher (Rust) | Lower (JS only) |
| Popularity | Growing fast | Mature, large community |
| Example apps | (new, few large ones) | VS Code, Slack, Discord |

### The Choice for SampleMind

We use **Tauri** because:
1. Native macOS integration is easier from Rust than from Node
2. Small app size — important for a "lightweight" DAW companion
3. Tauri 2 supports System Tray, native dialogs, and file access natively
4. Rust performance suits audio-related operations

### Tauri 2 — Key Concepts

#### IPC — Frontend communicates with Rust backend

```rust
// src-tauri/src/main.rs
use tauri::Manager;

#[tauri::command]
fn analyze_sample(file_path: String) -> Result<String, String> {
    // Call Python backend via std::process::Command
    // or run Rust-based analysis directly
    Ok(format!("Analyzed: {}", file_path))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![analyze_sample])
        .run(tauri::generate_context!())
        .expect("error running app");
}
```

```javascript
// Frontend (HTML/JS in dist/)
import { invoke } from '@tauri-apps/api/core';

async function analyzeFile(path) {
  const result = await invoke('analyze_sample', { filePath: path });
  console.log(result);
}
```

#### Events — Rust → Frontend communication

```rust
// Rust sends event to frontend
app.emit("analysis-complete", serde_json::json!({
    "bpm": 128.0,
    "key": "C maj",
    "mood": "euphoric"
})).unwrap();
```

```javascript
// Frontend listens
import { listen } from '@tauri-apps/api/event';

await listen('analysis-complete', (event) => {
  const { bpm, key, mood } = event.payload;
  updateUI(bpm, key, mood);
});
```

#### Native File Dialog (already set up in the project)

```rust
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
async fn pick_sample_folder(app: tauri::AppHandle) -> Option<String> {
    app.dialog()
        .file()
        .set_title("Select sample folder")
        .pick_folder()
        .await
        .map(|p| p.to_string())
}
```

#### System Tray (already configured)

```rust
use tauri::tray::{TrayIconBuilder, TrayIconEvent};

// Run SampleMind in background with tray icon
// Useful for FL Studio workflow — always available
TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .on_tray_icon_event(|tray, event| {
        if let TrayIconEvent::Click { .. } = event {
            // Show/hide window
        }
    })
    .build(app)?;
```

---

## 4. FL Studio Integration — macOS and Windows

### Integration Strategies — Simple to Advanced

```
Level 1: Filesystem integration (possible now)
  └─ Write/read files in FL Studio's sample folder
  └─ No API needed — works today

Level 2: Clipboard + MIDI (intermediate)
  └─ Copy sample info to clipboard
  └─ MIDI CC messages for parameter control

Level 3: macOS AppleScript / IPC (advanced)
  └─ Communicate with the FL Studio process
  └─ Automate actions in the app

Level 4: VST3 / AU Plugin (most integrated)
  └─ SampleMind as a plugin inside FL Studio
  └─ Requires C++ with JUCE framework
```

### Level 1 — Filesystem Integration (implement now)

FL Studio on macOS stores samples here:
```
~/Documents/Image-Line/FL Studio/
├── Projects/               # .flp project files
├── Presets/                # Preset files for instruments
└── Data/
    └── Projects/
        └── Samples/        # Standard sample folder
            └── Packs/      # Sample packs

# macOS user samples (common location)
~/Music/
└── SampleMind/             # Our own folder — FL Studio can point here
```

```python
# src/integrations/fl_studio_bridge.py (future)
import os
import shutil
from pathlib import Path

FL_SAMPLE_DIR = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Data" / "Projects" / "Samples"
SAMPLEMIND_DIR = Path.home() / "Music" / "SampleMind"

def export_to_fl_studio(sample_path: str, category: str, tags: list[str]) -> str:
    """
    Copy sample to FL Studio's sample folder with correct directory structure.
    FL Studio will then show it in its internal file browser.
    """
    dest = FL_SAMPLE_DIR / "SampleMind" / category / Path(sample_path).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_path, dest)

    # Write metadata sidecar file (XML or JSON alongside the WAV file)
    _write_metadata_sidecar(dest, tags)
    return str(dest)

def get_fl_studio_projects() -> list[dict]:
    """Find all .flp projects — useful for project context."""
    projects_dir = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Projects"
    return [
        {"name": p.stem, "path": str(p), "modified": p.stat().st_mtime}
        for p in projects_dir.glob("**/*.flp")
    ]
```

### Level 2 — macOS AppleScript Integration

AppleScript lets you automate macOS apps from Python/Rust. FL Studio has limited AppleScript support, but we can use it to:
- Switch to FL Studio
- Send keystrokes (open browser, search)
- Copy file paths to clipboard

```python
# src/integrations/applescript_bridge.py
import subprocess

def focus_fl_studio():
    """Bring FL Studio to front."""
    script = 'tell application "FL Studio" to activate'
    subprocess.run(["osascript", "-e", script])

def open_sample_browser_in_fl():
    """Press F8 to open sample browser in FL Studio."""
    script = '''
    tell application "System Events"
        tell process "FL Studio"
            key code 98  -- F8
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

def send_sample_path_to_clipboard(path: str):
    """Put sample path in clipboard — user can paste into FL."""
    subprocess.run(["pbcopy"], input=path.encode())
```

```rust
// In Tauri Rust backend — call AppleScript directly
use std::process::Command;

#[tauri::command]
fn focus_fl_studio() -> Result<(), String> {
    Command::new("osascript")
        .args(["-e", r#"tell application "FL Studio" to activate"#])
        .output()
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

### Level 3 — MIDI for FL Studio Control

FL Studio responds to MIDI CC messages. With a virtual MIDI port, SampleMind can send commands:

```python
# Requires: pip install python-rtmidi
# macOS: brew install rtmidi

import rtmidi

def create_virtual_midi_port():
    """Create a virtual MIDI port FL Studio can connect to."""
    midi_out = rtmidi.MidiOut()
    midi_out.open_virtual_port("SampleMind Control")
    return midi_out

def set_mixer_volume(port, track: int, volume: float):
    """Send CC message to set mixer volume."""
    # CC message: [0xB0 | channel, CC number, value 0-127]
    value = int(volume * 127)
    port.send_message([0xB0, track, value])

def trigger_sample_preview(port):
    """Send Note On to trigger sample preview."""
    port.send_message([0x90, 60, 100])  # Note C4, velocity 100
```

### Level 4 — VST3 / AU Plugin with JUCE (Long-term Goal)

JUCE is a C++ framework for building audio plugins. The SampleMind Pro vision:

```
┌──────────────────────────────────────────────────┐
│  FL Studio                                        │
│  ┌────────────────────────────────────────────┐  │
│  │  SampleMind AU/VST3 Plugin                 │  │
│  │  ┌────────────┐  ┌──────────────────────┐  │  │
│  │  │  JUCE UI   │  │  Python sidecar      │  │  │
│  │  │  (C++)     │◄─►  (analysis, AI, DB)  │  │  │
│  │  └────────────┘  └──────────────────────┘  │  │
│  │  Communication via local socket (IPC)       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

```cpp
// Plugin sidecar communication (future)
// JUCE sends JSON to Python backend via localhost socket

class SampleMindProcessor : public juce::AudioProcessor {
    juce::WebSocketClient client;

    void requestAnalysis(const juce::File& sample) {
        auto message = juce::JSON::toString(juce::var(juce::DynamicObject::Ptr(
            new juce::DynamicObject()
        )));
        client.send(R"({"action": "analyze", "path": ")" +
                    sample.getFullPathName() + R"("})");
    }
};
```

### macOS-specific Considerations

```
macOS requirements for audio apps:
1. Signing & Notarization — Apple requires signing for distribution
   → Tauri has built-in support: tauri.conf.json → bundle.macOS.signingIdentity

2. Hardened Runtime — Required for notarization
   → Requires entitlements for microphone, file access, etc.

3. Sandbox rules
   → Audio apps exempt from App Sandbox (but must declare audio entitlement)

4. AU (Audio Units) vs VST3
   → AU is Apple's own format — best support on macOS / Logic
   → VST3 works in FL Studio on macOS
   → Build BOTH for maximum compatibility
```

```xml
<!-- app/src-tauri/Info.plist additions for macOS -->
<key>NSMicrophoneUsageDescription</key>
<string>SampleMind needs microphone for live sample capture</string>
<key>com.apple.security.files.user-selected.read-write</key>
<true/>
<key>com.apple.security.assets.music.read-write</key>
<true/>
```

---

## 5. Phase 1 — Foundation & CLI ✅

**Status: Complete** — See `docs/en/phase-01-foundation.md`

### What Was Built

| Module | File | Function |
|--------|------|---------|
| Audio analysis | `src/samplemind/analyzer/audio_analysis.py` | BPM, key (chroma + tonnetz), energy, mood, instrument |
| AI classification | `src/samplemind/analyzer/classifier.py` | 9-feature rule-based classifier |
| CLI | `src/samplemind/cli/app.py` | Typer app: `import`, `analyze`, `list`, `search`, `tag`, `serve` |
| Database | `src/samplemind/data/database.py` | sqlite3: `~/.samplemind/library.db` |
| Web UI | `src/samplemind/web/app.py` | Flask: `localhost:5000` |
| Legacy entry | `src/main.py` | argparse CLI (still required by Tauri dev mode) |

### Running the CLI Tools

```bash
# Set up environment (use uv — not pip)
uv sync

# Analyze a sample
uv run samplemind analyze path/to/sample.wav

# Import an entire folder
uv run samplemind import ~/Music/MySamples/

# Search the library
uv run samplemind search --energy high --instrument kick

# Tag a sample manually
uv run samplemind tag sample --genre trap --mood dark

# Start web UI
uv run samplemind serve
```

### How Audio Analysis Works

```
WAV file
  └─ librosa.load() → y (float32 array), sr=22050
       ├─ BPM: beat_track() → tempo in BPM
       ├─ Key: chroma_cens() → 12 bands → root note
       │         tonnetz() → harmonic tension → major/minor
       └─ Classifier (9 features):
            ├─ rms                → energy: <0.015=low, <0.06=mid, ≥0.06=high
            ├─ centroid_norm      → spectral brightness (0–1, normalized)
            ├─ zcr                → zero-crossing rate → noise/percussive
            ├─ flatness           → tone vs white noise
            ├─ rolloff_norm       → high-frequency energy (0–1)
            ├─ onset_mean         → average rhythmic attack strength
            ├─ onset_max          → peak rhythmic attack
            ├─ low_freq_ratio     → bass content (energy below 300 Hz)
            └─ duration           → length → loop (>2s) vs one-shot
```

**Classifier output values** (exact strings stored in DB):

| Field | Values |
|-------|--------|
| `energy` | `"low"` `"mid"` `"high"` — ⚠️ **never `"medium"`** |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` |

---

## 6. Phase 2 — Audio Testing & Analysis ✅

**Status: Complete** — See `docs/en/phase-02-audio-analysis.md`

### What Was Built

- `tests/conftest.py` — synthetic WAV fixtures (soundfile + numpy, no real audio files)
- `tests/test_audio_analysis.py` — BPM, key, feature extraction tests
- `tests/test_classifier.py` — energy, mood, instrument classification tests
- CI coverage enforcement: `fail_under = 60` in pyproject.toml
- pytest markers: `slow`, `integration`, `macos`, `juce`, `benchmark`

### Test Commands

```bash
uv run pytest tests/ -v                                      # all tests
uv run pytest tests/ -m "not slow"                          # skip slow tests
uv run pytest tests/ -n auto                                # parallel (pytest-xdist)
uv run pytest --cov=samplemind --cov-report=term-missing    # coverage report
```

### Phase 2 Targets (not yet implemented)

- [ ] `src/samplemind/analyzer/fingerprint.py` — SHA-256 dedup fingerprinting
- [ ] `src/samplemind/analyzer/batch.py` — parallel batch analysis (ProcessPoolExecutor)
- [ ] `spectral_bandwidth` feature added to audio_analysis.py
- [ ] ML-based classifier (Phase 2+ target — scikit-learn RandomForest)

---

## 7. Phase 3 — Authentication & Authorization ✅

**Status: Complete** — Full JWT + RBAC auth system implemented

### What Was Built

| Component | File | Description |
|-----------|------|-------------|
| JWT handler | `src/samplemind/core/auth/jwt_handler.py` | Access + refresh tokens, `python-jose` |
| Password hashing | `src/samplemind/core/auth/password.py` | Direct `bcrypt` 5.x-compatible hashing |
| RBAC | `src/samplemind/core/auth/rbac.py` | Role-based permissions (viewer/owner/admin) |
| Dependencies | `src/samplemind/core/auth/dependencies.py` | FastAPI `Depends` helpers |
| User SQLModel | `src/samplemind/core/models/user.py` | Users table (id, email, role, hashed_password…) |
| User repository | `src/samplemind/data/repositories/user_repository.py` | CRUD for users |
| FastAPI auth routes | `src/samplemind/api/routes/auth.py` | `/register` `/login` `/refresh` `/me` `/change-password` |
| Flask auth UI | `src/samplemind/web/app.py` | Login/register pages, `@login_required` |
| Tauri token store | `app/src-tauri/src/main.rs` | `store_token` / `get_token` / `clear_token` IPC |
| Alembic migration | `migrations/versions/0001_create_users_table.py` | Baseline `users` schema |
| Test suite | `tests/test_auth.py` | 24 tests covering all auth paths |

### Auth Architecture

```
FastAPI /register → UserRepository.create() → bcrypt hash → SQLite users table
FastAPI /login    → bcrypt verify → JWT access+refresh tokens → client
FastAPI /me       → Bearer token → JWT decode → UserRepository.get_by_id()
Tauri JS          → invoke('store_token') → AuthTokenStore (Mutex<Option<String>>)
Flask session     → cookie-based session → @login_required decorator
```

### Key Technical Decisions

- **Direct `bcrypt`** instead of `passlib` — passlib 1.7.x cannot parse bcrypt 4.x/5.x version strings
- **`expire_on_commit=False`** in session — prevents `DetachedInstanceError` on ORM objects after commit
- **`StaticPool`** in tests — ensures in-memory SQLite shares one connection across threads
- **`datetime.now(UTC)`** throughout — replaces deprecated `datetime.utcnow()`

---

## 8. Phase 4 — Database & Data Layer 🔄

**Status: In Progress** — See `docs/en/phase-03-database.md`

### Goal

Replace the raw `sqlite3` implementation in `database.py` with SQLModel + Alembic + Repository pattern
for the `samples` table. The `users` table is already on SQLModel (Phase 3).

### What Was Built

- `src/samplemind/data/orm.py` — shared SQLModel engine + session factory (used by auth)
- `migrations/versions/0001_create_users_table.py` — users schema baseline
- WAL mode + performance PRAGMAs on every connection (via SQLAlchemy event listener)

### In Progress / Targets

- [x] SQLModel engine + `init_orm()` (done — `data/orm.py`)
- [x] Alembic configured with `render_as_batch=True` for SQLite
- [ ] `src/samplemind/core/models/sample.py` — `Sample` SQLModel table + `SampleCreate`/`SampleUpdate`
- [ ] `src/samplemind/data/repositories/sample_repository.py` — `SampleRepository`
- [ ] `migrations/versions/0002_create_samples_table.py` — samples schema migration
- [ ] CLI commands migrated from `database.py` to `SampleRepository`
- [ ] Flask web routes migrated from `database.py` to `SampleRepository`
- [ ] `database.py` retired (kept as legacy fallback until full cutover)

---

## 9. Phase 5 — CLI Modernization 📋

**Status: Planned** — See `docs/en/phase-04-cli.md`

### Goal

Ensure all 6+ CLI commands use the `SampleRepository` (Phase 4) and support `--json` output.
Add `stats` and `duplicates` commands.

### Targets

- [ ] All import/list/search/tag commands use `SampleRepository`
- [ ] `stats` command — library statistics (total, by instrument, by mood, by energy)
- [ ] `duplicates` command — SHA-256 fingerprint dedup
- [ ] `--workers` flag on `import` — `ProcessPoolExecutor` batch analysis
- [ ] Shell completion via `samplemind --install-completion`

---

## 10. Phase 6 — Web UI Improvements 📋

**Status: Planned** — See `docs/en/phase-05-web-ui.md`

### Goal

Upgrade the Flask web UI with HTMX-powered live updates, Server-Sent Events (SSE) for import
progress, and waveform preview using wavesurfer.js.

### Targets

- [ ] HTMX inline search (no page reload)
- [ ] SSE progress stream during import (`/api/import/stream`)
- [ ] Waveform preview via wavesurfer.js
- [ ] Dark/light theme toggle
- [ ] Responsive mobile layout

---

## 11. Phase 7 — Desktop App (Tauri + Svelte 5) 📋

**Status: Foundation complete** — See `docs/en/phase-06-desktop-app.md`

### What Was Built (Foundation)

- `app/src-tauri/src/main.rs` — Tauri 2 app with Rust commands:
  - `pick_folder` — native folder dialog (tauri-plugin-dialog)
  - `is_directory` — path check helper
  - `store_token` / `get_token` / `clear_token` — JWT token store (Phase 3)
- System tray with Show/Quit menu
- Dev mode: Flask spawned on port 5174, Tauri WebView loads it
- Bundle targets: macOS (dmg+app), Windows (msi+nsis), Linux (appimage+deb)

### Targets (Phase 7)

- [ ] Svelte 5 frontend replaces Flask WebView
- [ ] `import_folder` IPC command — calls Python sidecar `samplemind import --json`
- [ ] `search_samples` IPC command — calls `samplemind search --json`
- [ ] `SampleTable` Svelte component with sorting and filtering
- [ ] `WaveformPlayer` component using wavesurfer.js
- [ ] `ImportPanel` with drag-and-drop and progress
- [ ] `stores/library.svelte.ts` — Svelte 5 Runes state management

### Build and Run

```bash
cd app/
pnpm install

# Dev mode (spawns Flask on port 5174 automatically)
pnpm tauri dev

# Production build
pnpm tauri build
# Output: app/src-tauri/target/release/bundle/
#   macOS:   SampleMind.app + SampleMind.dmg
#   Windows: SampleMind.exe + SampleMind.msi
```

---

## 12. Phase 8 — FL Studio Automation 📋

**Status: Planned** — See `docs/en/phase-07-fl-studio.md`

### Targets

- [ ] Filesystem export to FL Studio sample folder
- [ ] AppleScript automation (focus FL Studio, open browser)
- [ ] Clipboard path copy for drag-and-drop into FL Studio
- [ ] MIDI CC messages via `python-rtmidi` (optional)

---

## 13. Phase 9 — VST3/AU Plugin 🔮

**Status: Not started — requires C++ / JUCE knowledge**

### Learning Path to Plugin Development

```
Step 1: Learn C++ basics
  └─ Resource: "The C++ Programming Language" by Stroustrup
  └─ Focus: classes, templates, memory management, smart pointers

Step 2: Install and learn JUCE
  └─ Download: https://juce.com/
  └─ Start with: JUCE Audio Plugin Tutorial
  └─ Build a simple gain plugin as exercise

Step 3: Create SampleMind plugin with Python sidecar
  └─ Plugin UI: JUCE Component (C++)
  └─ Analysis backend: Python subprocess / socket
  └─ IPC: Unix domain socket (macOS) or named pipe (Windows)

Step 4: Sign and distribute
  └─ macOS: Apple Developer Program ($99/year)
  └─ Notarization via Xcode or notarytool
```

### Simple JUCE Plugin Structure (reference)

```cpp
// PluginProcessor.h — Audio Plugin entry point
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class SampleMindProcessor : public juce::AudioProcessor {
public:
    SampleMindProcessor();

    // These must be implemented:
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    // Plugin info
    const juce::String getName() const override { return "SampleMind"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }

    // Analysis function — calls Python sidecar
    void analyzeSampleAsync(const juce::File& file);

private:
    // Socket connection to Python backend
    std::unique_ptr<juce::StreamingSocket> backendSocket;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindProcessor)
};
```

### Python Sidecar Server (for plugin IPC)

```python
# scripts/plugin_server.py — Runs as background process by plugin
import socket
import json
from src.analyzer.audio_analysis import analyze_file

HOST = "127.0.0.1"
PORT = 9876

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"SampleMind backend running on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096).decode()
                request = json.loads(data)

                if request["action"] == "analyze":
                    result = analyze_file(request["path"])
                    conn.send(json.dumps(result).encode())
```

---

## 14. Phase 10 — Sample Packs 📋

**Status: Planned** — See `docs/en/phase-09-sample-packs.md`

---

## 15. Phase 11 — Production & Release 📋

**Status: Planned** — See `docs/en/phase-10-production.md`

---

## 16. Community and Cloud Sharing 🔮

**Status: Concept**

### Sample Pack System

```
SampleMind Pack Format (.smpack):
├── manifest.json       # Metadata: name, BPM, genre, keys, tags
├── samples/
│   ├── kick_128.wav
│   └── bass_dark.wav
└── preview.mp3         # 30-second preview mixdown
```

```json
// manifest.json example
{
  "name": "Dark Trap Kit Vol.1",
  "version": "1.0.0",
  "author": "lchtangen",
  "bpm_range": [130, 145],
  "keys": ["C min", "F# min"],
  "genres": ["trap", "dark"],
  "samples": [
    {
      "file": "samples/kick_128.wav",
      "bpm": 128,
      "key": "C min",
      "energy": "high",
      "mood": "dark",
      "instrument": "kick",
      "tags": ["808", "sub", "punchy"]
    }
  ],
  "created": "2025-08-01",
  "samplemind_version": "0.3.0"
}
```

### GitHub-based Distribution

```yaml
# .github/workflows/publish-pack.yml
name: Publish Sample Pack

on:
  push:
    tags:
      - 'pack-v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create .smpack archive
        run: |
          python scripts/pack_builder.py --output dist/pack.smpack

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/pack.smpack
          generate_release_notes: true
```

---

## 16. Phase 12 — Semantic Search & Vector Embeddings 📋

**Status: Planned** — Prerequisites: Phase 4 (Database) ✅, Phase 5 (CLI), Phase 11 (Release)

### Why Semantic Search?

Rule-based search (`energy="high"`, `instrument="kick"`) misses *intent*.
Semantic search lets users type **"punchy 808 with sub tail"** or **"bright pluck that feels euphoric"**
and get ranked results — even if those exact words aren't in the filename or tags.

### Architecture

```
Audio file imported
  └─► librosa feature extraction (existing)
  └─► CLAP encoder (HuggingFace ClapModel) → 512-dim float32 embedding
        └─► sqlite-vec virtual table (ann_samples) ← ANN index
              └─► KNN query: "find dark atmospheric pads" → text embedding → cosine distance
```

### Implementation Plan

| Task | File | Description |
|------|------|-------------|
| Add embeddings column | `migrations/versions/0003_add_embeddings.py` | `embedding BLOB` in samples table |
| CLAP encoder | `src/samplemind/analyzer/embeddings.py` | `encode_audio()` + `encode_text()` |
| sqlite-vec integration | `src/samplemind/data/vector_store.py` | ANN index create, insert, query |
| Semantic search API | `src/samplemind/api/routes/search.py` | `POST /search/semantic` |
| CLI command | `src/samplemind/cli/commands/search.py` | `samplemind search "dark kick" --semantic` |
| Re-index command | `src/samplemind/cli/commands/embeddings.py` | `samplemind embeddings rebuild` |

### Key Code Patterns

```python
# src/samplemind/analyzer/embeddings.py
import sqlite_vec                        # C extension — no extra infra
from transformers import ClapModel, ClapProcessor

model = ClapModel.from_pretrained("laion/larger_clap_music")
processor = ClapProcessor.from_pretrained("laion/larger_clap_music")

def encode_audio(path: str) -> list[float]:
    """Return 512-dim float32 CLAP embedding for an audio file."""
    inputs = processor(audios=load_audio(path), return_tensors="pt", sampling_rate=48000)
    with torch.no_grad():
        return model.get_audio_features(**inputs).squeeze().tolist()

def encode_text(query: str) -> list[float]:
    """Return 512-dim float32 CLAP embedding for a text query."""
    inputs = processor(text=[query], return_tensors="pt", padding=True)
    with torch.no_grad():
        return model.get_text_features(**inputs).squeeze().tolist()
```

```python
# src/samplemind/data/vector_store.py
import sqlite_vec
import struct, sqlite3

def create_vec_table(conn: sqlite3.Connection) -> None:
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS ann_samples USING vec0(embedding float[512])")

def semantic_search(conn: sqlite3.Connection, query_text: str, k: int = 10) -> list[int]:
    embedding = encode_text(query_text)
    blob = struct.pack(f"{len(embedding)}f", *embedding)
    rows = conn.execute(
        "SELECT rowid, distance FROM ann_samples WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
        (blob, k)
    ).fetchall()
    return [r[0] for r in rows]
```

### Testing

```python
# tests/test_semantic_search.py (future)
from hypothesis import given, strategies as st

@given(st.text(min_size=3, max_size=100))
def test_semantic_search_never_crashes(query):
    """Property: any query string should return a valid list, never raise."""
    results = semantic_search_text(query, k=5)
    assert isinstance(results, list)
    assert len(results) <= 5
```

---

## 17. Phase 13 — AI Agent Automation 📋

**Status: Planned** — Prerequisites: Phase 12 (Semantic Search), pydantic-ai installed ✅

### Why AI Agents?

Manual tagging doesn't scale to 10,000+ sample libraries.
An agent can:
- **Auto-tag** samples using CLAP embeddings + LLM reasoning ("this sounds like a snare in a reverb room")
- **Answer natural-language questions** ("how many dark kicks do I have under 130 BPM?")
- **Suggest samples** for a project context ("I'm making a lofi hip-hop beat at 90 BPM in C minor — what fits?")
- **Batch import + organize** an entire folder with smart genre/mood inference

### Architecture

```
User query (CLI or Tauri)
  └─► pydantic-ai Agent (model = claude-3-5-sonnet or ollama/llama3.3)
        └─► Tools (Python functions auto-discovered from type annotations):
              ├── search_samples(query, energy, instrument, bpm_min, bpm_max) → list[Sample]
              ├── semantic_search(description) → list[Sample]  ← sqlite-vec ANN
              ├── get_library_stats() → LibraryStats
              ├── tag_sample(path, genre, mood, energy, tags) → bool
              ├── analyze_file(path) → AudioFeatures
              └── import_folder(path) → ImportResult
        └─► Structured response (Pydantic model → JSON → CLI/Tauri)
```

### Implementation Plan

```python
# src/samplemind/agents/library_agent.py
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.ollama import OllamaModel
from samplemind.core.config import get_settings
from samplemind.data.repositories.sample_repository import SampleRepository

def build_agent(use_local: bool = False) -> Agent:
    """Build the SampleMind library agent.

    use_local=True: use Ollama (llama3.3 — no API key needed, runs offline)
    use_local=False: use Claude claude-3-5-sonnet-latest (better reasoning)
    """
    model = OllamaModel("llama3.3") if use_local else AnthropicModel("claude-3-5-sonnet-latest")

    agent = Agent(
        model=model,
        system_prompt=(
            "You are SampleMind, an AI assistant for music producers. "
            "You help organize, search, and discover audio samples. "
            "Always return structured data. Be concise and musical."
        ),
    )

    @agent.tool
    def search_samples(query: str, energy: str | None = None, instrument: str | None = None) -> list[dict]:
        """Search the sample library by filename, tags, energy, or instrument."""
        results = SampleRepository.search(query=query, energy=energy, instrument=instrument)
        return [{"id": s.id, "filename": s.filename, "bpm": s.bpm, "mood": s.mood} for s in results[:10]]

    @agent.tool
    def get_library_stats() -> dict:
        """Get statistics about the current sample library."""
        return {"total": SampleRepository.count()}

    return agent
```

### CLI Integration

```bash
# Interactive agent chat
uv run samplemind agent chat

# Single question (pipe-friendly)
uv run samplemind agent ask "find me 5 dark kicks between 120-140 BPM"

# Auto-tag an entire imported folder
uv run samplemind agent autotag ~/Music/NewSamples/ --model ollama/llama3.3

# JSON output for Tauri IPC
uv run samplemind agent ask "show library stats" --json
```

### Model Provider Support (via pydantic-ai)

| Provider | When to use | Config |
|----------|------------|--------|
| `claude-3-5-sonnet-latest` | Best reasoning, complex queries | `ANTHROPIC_API_KEY` env var |
| `gpt-4o` | OpenAI users | `OPENAI_API_KEY` env var |
| `ollama/llama3.3` | Fully offline, no API key | Ollama running locally |
| `ollama/qwen2.5-coder` | Code-heavy tool use | Ollama running locally |
| `gemini-2.0-flash` | Fast, cheap, large context | `GOOGLE_API_KEY` env var |

---

## 18. Backlog and Future Ideas

| Idea | Complexity | Value | Priority |
|------|------------|-------|----------|
| Audio fingerprint matching (avoid duplicates) | Medium | High | P1 |
| Automatic BPM match to project tempo | Medium | High | P1 |
| Mood wheel UI for sample search | Medium | High | P2 |
| Smart compressor/EQ suggestions via AI | High | Medium | P2 |
| Voice-based search ("find dark kicks") | High | High | P2 |
| AI assistant that suggests samples from sketch | Very high | Very high | P3 |
| Version control for sample edits | Medium | Medium | P3 |
| Automated tagging of older libraries | Low | High | P1 |
| Real-time analysis during recording | High | Medium | P3 |
| Cloud sync of library and metadata | High | High | P3 |

### Audio Fingerprint Matching (prioritized)

```python
# src/analyzer/fingerprint.py (future)
import librosa
import numpy as np
from hashlib import sha256

def compute_fingerprint(file_path: str) -> str:
    """
    Compute an acoustic fingerprint for a sample.
    Used to detect duplicates even when filenames differ.

    Method: chromagram hash — robust against volume changes and light EQ.
    """
    y, sr = librosa.load(file_path, duration=10.0)

    # Chroma features are stable and pitch-independent enough for matching
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    # Quantize to 4-bit for robustness against small variations
    quantized = (chroma * 15).astype(np.uint8)

    return sha256(quantized.tobytes()).hexdigest()[:16]

def find_duplicates(sample_paths: list[str]) -> list[tuple[str, str]]:
    """Find all sample pairs that are acoustically identical."""
    fingerprints = {}
    duplicates = []

    for path in sample_paths:
        fp = compute_fingerprint(path)
        if fp in fingerprints:
            duplicates.append((fingerprints[fp], path))
        else:
            fingerprints[fp] = path

    return duplicates
```

---

## 19. Long-term Vision 2026–2030

```
SampleMind AI Product Suite (2026–2030):

┌──────────────────────────────────────────────────────────────────────────┐
│                        SampleMind Ecosystem                              │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │  SampleMind │  │  SampleMind │  │  SampleMind │  │  SampleMind  │   │
│  │   Desktop   │  │   Plugin    │  │    Cloud    │  │    Agent     │   │
│  │ (Tauri 2+)  │  │ (VST3 / AU) │  │  (Web App)  │  │  (CLI + API) │   │
│  │             │  │             │  │             │  │              │   │
│  │ Svelte 5    │  │ JUCE 8      │  │ Sync, share │  │ pydantic-ai  │   │
│  │ Runes UI    │  │ C++ + IPC   │  │ collaborate │  │ Ollama local │   │
│  │ Waveform    │  │ In FL Studio│  │ AI mastering│  │ auto-tag,    │   │
│  │ Semantic    │  │ and other   │  │ pack market │  │ Q&A, suggest │   │
│  │ search      │  │ DAWs        │  │ place       │  │              │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘   │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                          Shared Python Backend                           │
│        FastAPI + SQLModel + sqlite-vec + pydantic-ai + Alembic          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Milestone Timeline (2026–2030)

| Timeline | Milestone | Key Technologies |
|----------|-----------|-----------------|
| **Q2 2026** | Phase 5–6: CLI + Web UI polished | Typer, HTMX, SSE, Rich |
| **Q3 2026** | Phase 7: Tauri + Svelte 5 desktop app ships | Tauri 2, Svelte 5 Runes, pnpm |
| **Q4 2026** | Phase 8: FL Studio filesystem integration | AppleScript, Rust, clipboard |
| **Q1 2027** | Phase 9: VST3/AU plugin prototype | JUCE 8, Unix socket IPC |
| **Q2 2027** | Phase 12: Semantic search live | sqlite-vec, CLAP embeddings, sentence-transformers |
| **Q3 2027** | Phase 13: AI agent CLI + API | pydantic-ai, Ollama (offline), Claude/GPT (cloud) |
| **Q4 2027** | Phase 11: macOS + Windows production release | Tauri bundle, PyInstaller sidecar, notarization |
| **2028** | SampleMind Cloud beta | FastAPI cloud, PostgreSQL + pgvector, Stripe |
| **2028** | Python 3.14 free-threaded migration | PEP 703 no-GIL → true parallel librosa workers |
| **2029** | Mobile companion app | Tauri Mobile (iOS/Android), React Native alternative |
| **2030** | SampleMind Pro: AI mastering & generation | On-device diffusion models, ControlNet for audio |

### AI Technology Roadmap (Audio-Specific)

| Year | Technology | Use Case | Notes |
|------|-----------|----------|-------|
| 2026 | CLAP (ClapModel via HuggingFace transformers) | Zero-shot instrument classification + semantic search | numpy 2.x compatible via transformers ≥4.40 |
| 2026 | sqlite-vec | Sub-ms ANN search, no external vector DB | Pure C, works in Tauri sidecar bundle |
| 2026 | pydantic-ai + Ollama | Offline AI agent, auto-tag, Q&A | Runs llama3.3 / qwen2.5 locally |
| 2027 | AudioBox (Meta) / Stable Audio 2 | AI sample generation ("generate a 4-bar lofi loop") | Inference API or local |
| 2027 | XTTS-v2 / Kokoro-TTS | Audio description narration for accessibility | Local inference |
| 2028 | Python 3.14 free-threaded | True parallel librosa batch processing (no GIL) | 2–8× speedup on multi-core |
| 2028 | Diffusion-based source separation | Stem splitting (vocals/drums/bass) inside SampleMind | Building on Demucs v5+ |
| 2029 | On-device LLM (Apple Neural Engine) | mlx-based inference on Apple Silicon, no internet | mlx-lm, llama.cpp Metal |
| 2030 | Audio ControlNet | AI-guided sample morphing and stem-aware effects | Research → production |

### Learning Resources (2026 Edition)

| Topic | Resource |
|-------|---------|
| Tauri 2 docs | https://v2.tauri.app/start/ |
| Svelte 5 Runes | https://svelte-5-preview.vercel.app/docs/introduction |
| pydantic-ai docs | https://ai.pydantic.dev/ |
| sqlite-vec docs | https://alexgarcia.xyz/sqlite-vec/ |
| CLAP model (HuggingFace) | https://huggingface.co/laion/larger_clap_music |
| Ollama local models | https://ollama.com/library |
| JUCE 8 tutorials | https://juce.com/learn/tutorials/ |
| librosa documentation | https://librosa.org/doc/0.11.0/ |
| Rust async book | https://rust-lang.github.io/async-book/ |
| uv documentation | https://docs.astral.sh/uv/ |
| Logfire observability | https://logfire.pydantic.dev/ |

---

## 20. Technology Decision Log

| Technology | Replaces | Rationale | Status |
|---|---|---|---|
| **python-jose** | PyJWT | RS256 + HS256 support; used in Beta auth | ✅ Live |
| **bcrypt (direct)** | passlib[bcrypt] | passlib 1.7.x can't parse bcrypt 4.x/5.x version strings | ✅ Live |
| **FastAPI** | Flask (for API) | Async, auto OpenAPI docs, Pydantic v2 native | ✅ Live |
| **SQLModel** | raw sqlite3 | Type-safe ORM (SQLAlchemy 2 + Pydantic v2 in one class) | ✅ Live |
| **Alembic** | `_migrate()` hack | Reversible, versioned schema migrations; CI-verified | ✅ Live |
| **platformdirs** | hardcoded paths | Cross-platform app data dirs (macOS/Linux/Windows) | ✅ Live |
| **StaticPool** in tests | thread-local pools | In-memory SQLite shared across threads — critical for FastAPI tests | ✅ Live |
| **sqlite-vec** | Qdrant / pgvector | Zero-infra ANN search inside existing SQLite DB; C extension | ✅ Installed |
| **pydantic-ai** | LangChain | Simpler, type-safe, model-agnostic agent framework from Pydantic team | ✅ Installed |
| **hypothesis** | manual edge-case tests | Property-based fuzzing finds edge cases no human would write | ✅ Installed |
| **pyright** | mypy | Rust-based type checker; 10–100× faster; first-class Pydantic v2 support | ✅ Installed |
| **Logfire** | print/logging | OpenTelemetry-native structured observability; auto-instruments FastAPI | 📋 Phase 11 |
| **Ruff ≥0.15** | flake8+isort+black | Single binary; adds ANN + S + PERF + LOG rule sets | ✅ Live |
| **CLAP (HuggingFace)** | laion-clap | numpy 2.x compatible; zero-shot audio classification via text | 📋 Phase 12 |
| **Ollama** | OpenAI API | Fully offline LLM inference; llama3.3, qwen2.5, gemma3 | 📋 Phase 13 |
| **Python 3.14 no-GIL** | GIL-limited threads | PEP 703 free-threaded mode → true parallel audio workers | 📋 2028 |

---

---

*Last updated: March 2026 — v0.2.0 — Active development in progress*
