# SampleMind AI — Roadmap & Technical Guide

> **Main goal:** Build an AI-powered sample library and DAW companion for FL Studio on macOS (and Windows). The tool should analyze, tag, organize, and export samples — and ultimately integrate directly with FL Studio via native macOS mechanisms or plugin APIs.

---

## Table of Contents

1. [Project Overview and Architecture](#1-project-overview-and-architecture)
2. [Tech Stack — What We Use and Why](#2-tech-stack--what-we-use-and-why)
3. [Tauri vs Electron — Desktop UI Choice](#3-tauri-vs-electron--desktop-ui-choice)
4. [FL Studio Integration — macOS and Windows](#4-fl-studio-integration--macos-and-windows)
5. [Phase 1 — CLI Prototype ✅](#5-phase-1--cli-prototype-)
6. [Phase 2 — AI Analysis and Web UI 🔄](#6-phase-2--ai-analysis-and-web-ui-)
7. [Phase 3 — Desktop App with Tauri 🔄](#7-phase-3--desktop-app-with-tauri-)
8. [Phase 4 — FL Studio Plugin / VST3 / AU 🔮](#8-phase-4--fl-studio-plugin--vst3--au-)
9. [Phase 5 — Community and Cloud Sharing 🔮](#9-phase-5--community-and-cloud-sharing-)
10. [Backlog and Future Ideas](#10-backlog-and-future-ideas)
11. [Long-term Vision 2026+](#11-long-term-vision-2026)

---

## 1. Project Overview and Architecture

```
SampleMind-AI/
├── src/                        # Python backend (analysis, CLI, web)
│   ├── analyzer/
│   │   ├── audio_analysis.py   # librosa-based BPM, key, mood analysis
│   │   └── classifier.py       # Rule-based AI: energy, mood, instrument
│   ├── cli/
│   │   ├── analyze.py          # CLI: analyze a file
│   │   ├── importer.py         # CLI: import samples to database
│   │   ├── library.py          # CLI: search and manage library
│   │   └── tagger.py           # CLI: manual tagging
│   └── web/
│       ├── app.py              # Flask web app (local UI)
│       ├── templates/          # HTML Jinja2 templates
│       └── static/             # CSS, JS, waveform components
├── app/                        # Tauri desktop app (Rust + Web frontend)
│   ├── src-tauri/
│   │   ├── Cargo.toml          # Rust dependencies
│   │   ├── tauri.conf.json     # Tauri configuration
│   │   └── src/main.rs         # Rust backend code
│   ├── dist/                   # Compiled frontend (HTML/JS/CSS)
│   └── package.json            # Node/pnpm scripts for Tauri CLI
├── scripts/                    # Helper scripts
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
└── main.py                     # Main entry point
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

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Audio analysis | Python + librosa | Industry standard for audio ML. Provides BPM, key, spectral features. |
| AI classification | NumPy + rule-based (now) → scikit-learn / transformers (future) | Start simple, scale to ML. |
| Database | SQLite (via Python) | File-based, no server. Perfect for local desktop app. |
| CLI | Python argparse / click | Fast to prototype and test. |
| Web UI (local) | Flask + Jinja2 + HTMX | Simple local web server. HTMX provides reactivity without React/Vue overhead. |
| Desktop app | **Tauri 2** (Rust + Web) | Small bundle size, native performance, macOS-integrated. See section 3. |
| Desktop frontend | HTML + CSS + JS (vanilla or Svelte) | Tauri requires web frontend. Svelte is lightweight. |
| macOS integration | AppleScript / Swift / Rust | For FL Studio communication. See section 4. |
| Plugin (future) | JUCE (C++) + Python sidecar | VST3/AU plugin that communicates with Python backend. |

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

## 5. Phase 1 — CLI Prototype ✅

**Status: Complete**

### What Was Built

| Module | File | Function |
|--------|------|---------|
| Audio analysis | `src/analyzer/audio_analysis.py` | BPM, key (chroma + tonnetz), mood |
| AI classification | `src/analyzer/classifier.py` | energy, mood, instrument via 8 audio features |
| Import CLI | `src/cli/importer.py` | Import WAV files to database |
| Analysis CLI | `src/cli/analyze.py` | Analyze single file or folder |
| Library CLI | `src/cli/library.py` | Search and manage samples |
| Tagger | `src/cli/tagger.py` | Manual tagging of samples |

### Running the CLI Tools

```bash
# Set up environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Analyze a sample
python main.py analyze path/to/sample.wav

# Import an entire folder
python main.py import ~/Music/MySamples/

# Search the library
python main.py library search --mood dark --instrument kick

# Tag a sample manually
python main.py tag sample.wav --tags "trap,heavy,808"
```

### How Audio Analysis Works

```
WAV file
  └─ librosa.load() → y (audio wave), sr (sample rate)
       ├─ BPM: beat_track() → tempo in BPM
       ├─ Key: chroma_cens() → 12 frequency bands → highest = root note
       │         tonnetz() → harmonic tension → major/minor
       └─ Classifier (8 features):
            ├─ rms                → energy/loudness
            ├─ spectral_centroid  → bright/dark tone
            ├─ zero_crossing_rate → noise/percussive character
            ├─ spectral_flatness  → tone vs white noise
            ├─ spectral_rolloff   → high-frequency energy
            ├─ onset_strength     → rhythmic attacks
            ├─ low_freq_ratio     → bass content
            └─ duration           → length → loop vs one-shot
```

### Remaining Tasks in Phase 1

- [ ] `organizer` module: automatic folder structure based on metadata
  ```
  ~/Music/SampleMind/
  ├── Drums/
  │   ├── Kicks/
  │   │   └── kick_heavy_128bpm_Cmaj.wav
  │   └── Snares/
  └── Bass/
      └── bass_dark_140bpm_Fmin.wav
  ```
- [ ] Test data suite with known samples and expected results
- [ ] `pytest` suite for analyzer and classifier

---

## 6. Phase 2 — AI Analysis and Web UI 🔄

**Status: Partially complete**

### What Is Missing

#### 2a. ML-based classification (replacement for rule-based)

The current `classifier.py` uses hardcoded thresholds. The next step is a trained model:

```python
# Future: src/analyzer/ml_classifier.py
from sklearn.ensemble import RandomForestClassifier
import joblib

class MLClassifier:
    def __init__(self, model_path="models/classifier.pkl"):
        self.model = joblib.load(model_path)

    def predict(self, features: dict) -> dict:
        X = [[
            features["rms"],
            features["centroid_norm"],
            features["zcr"],
            features["flatness"],
            features["rolloff_norm"],
            features["onset_mean"],
            features["low_freq_ratio"],
            features["duration"]
        ]]
        instrument = self.model.predict(X)[0]
        return {"instrument": instrument}

    # Training workflow:
    # 1. Create labeled dataset (CSV with features + labels)
    # 2. python scripts/train_classifier.py
    # 3. Save model as models/classifier.pkl
```

#### 2b. Web UI improvements

```
Current Flask Web UI:
  src/web/app.py → localhost:5000

Missing:
  [ ] Drag & drop sample import (Dropzone.js or native HTML5)
  [ ] Waveform preview (Wavesurfer.js)
  [ ] HTMX for live updates without page reload
  [ ] Voice-based search ("find dark kicks with high energy")
```

```html
<!-- Waveform preview with Wavesurfer.js -->
<!-- templates/sample_detail.html -->
<div id="waveform"></div>
<button id="play">▶ Play</button>

<script src="https://unpkg.com/wavesurfer.js@7"></script>
<script>
const ws = WaveSurfer.create({
    container: '#waveform',
    waveColor: '#6366f1',
    progressColor: '#4f46e5',
    url: '/static/samples/{{ sample.filename }}'
});
document.getElementById('play').addEventListener('click', () => ws.playPause());
</script>
```

```html
<!-- Drag & drop with HTMX -->
<!-- templates/import.html -->
<div id="drop-zone"
     hx-post="/api/import"
     hx-encoding="multipart/form-data"
     hx-trigger="drop"
     hx-target="#results">
  Drop samples here
</div>
```

---

## 7. Phase 3 — Desktop App with Tauri 🔄

**Status: Early phase — Tauri 2 shell is set up**

### Current Tauri Setup

```
app/
├── src-tauri/
│   ├── Cargo.toml          # Tauri 2 + dialog + tray-icon
│   ├── tauri.conf.json     # Window: 1280x840, system tray
│   └── src/main.rs         # Rust entry point
├── dist/                   # Frontend (not built yet)
└── package.json            # Tauri CLI scripts
```

### Build and Run the Tauri App

```bash
# Requires Rust installed: https://rustup.rs/
# macOS: xcode-select --install

cd app/
pnpm install   # or: npm install

# Run in dev mode (hot reload)
pnpm tauri dev

# Build for distribution
pnpm tauri build
# Output: app/src-tauri/target/release/bundle/
#   macOS: SampleMind AI.app + .dmg
#   Windows: .exe + .msi
```

### Plan: Frontend Architecture for the Tauri App

We will build the frontend with **Svelte** (lightweight, compiled, fast):

```bash
# Set up Svelte in the Tauri project
cd app/
npm create vite@latest . -- --template svelte
npm install
```

```
app/
├── src/                    # Svelte frontend
│   ├── App.svelte          # Main component
│   ├── lib/
│   │   ├── SampleBrowser.svelte   # List and filter samples
│   │   ├── WaveformPlayer.svelte  # Wavesurfer.js preview
│   │   ├── TagEditor.svelte       # Tag editing
│   │   └── ImportDropzone.svelte  # Drag & drop import
│   └── tauri.js            # Tauri API wrappers
├── src-tauri/
└── package.json
```

### Key Tauri Commands to Implement

```rust
// src-tauri/src/main.rs — commands the frontend can call

#[tauri::command]
async fn scan_folder(path: String) -> Result<Vec<SampleInfo>, String> {
    // Call Python script or use Rust-based scanning
    todo!()
}

#[tauri::command]
async fn analyze_sample(path: String) -> Result<AnalysisResult, String> {
    // Spawn Python process: python main.py analyze <path>
    let output = std::process::Command::new("python")
        .args(["main.py", "analyze", &path])
        .output()
        .map_err(|e| e.to_string())?;

    let json_str = String::from_utf8(output.stdout).map_err(|e| e.to_string())?;
    serde_json::from_str(&json_str).map_err(|e| e.to_string())
}

#[tauri::command]
async fn export_to_fl_studio(sample_id: u32) -> Result<String, String> {
    // Copy file to FL Studio sample folder
    todo!()
}
```

### macOS-specific Tauri Configuration

```json
// tauri.conf.json — macOS bundle settings
{
  "bundle": {
    "macOS": {
      "minimumSystemVersion": "12.0",
      "signingIdentity": "Developer ID Application: Your Name",
      "entitlements": "entitlements.plist",
      "exceptionDomain": "",
      "frameworks": []
    },
    "category": "MusicApplication"
  }
}
```

---

## 8. Phase 4 — FL Studio Plugin / VST3 / AU 🔮

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

## 9. Phase 5 — Community and Cloud Sharing 🔮

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

## 10. Backlog and Future Ideas

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

## 11. Long-term Vision 2026+

```
SampleMind AI Product Suite:

┌─────────────────────────────────────────────────────────┐
│                  SampleMind Ecosystem                    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  SampleMind  │  │  SampleMind  │  │  SampleMind  │  │
│  │   Desktop    │  │   Plugin     │  │    Cloud     │  │
│  │  (Tauri App) │  │ (VST3 / AU)  │  │  (Web App)   │  │
│  │              │  │              │  │              │  │
│  │  Organize,   │  │  Directly in │  │  Share packs,│  │
│  │  analyze,    │  │  FL Studio   │  │  backup,     │  │
│  │  search,     │  │  and DAWs    │  │  collaborate │  │
│  │  export      │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                    Shared backend:                       │
│              Python AI + SQLite + REST API               │
└─────────────────────────────────────────────────────────┘
```

### Milestones Toward SampleMind Pro

| Timeline | Goal |
|----------|------|
| Q1 2026 | Complete Tauri desktop app with Svelte UI and Python integration |
| Q2 2026 | FL Studio filesystem integration + sample export workflow |
| Q3 2026 | First JUCE plugin prototype (AU/VST3) |
| Q4 2026 | macOS App Store or direct distribution with notarization |
| 2027 | SampleMind Cloud beta — sharing, collaboration, AI mastering |

### Learning Resources

| Topic | Resource |
|-------|---------|
| Tauri 2 docs | https://v2.tauri.app/start/ |
| Svelte tutorial | https://learn.svelte.dev/ |
| JUCE beginner guide | https://juce.com/learn/tutorials/ |
| Audio plugin development | "Designing Software Synthesizer Plugins in C++" by Will Pirkle |
| librosa documentation | https://librosa.org/doc/ |
| Rust beginner book | https://doc.rust-lang.org/book/ |
| macOS plugin signing | https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution |

---

*Last updated: March 2026 — Active development in progress*
