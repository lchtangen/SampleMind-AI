# SampleMind AI — Roadmap & Teknisk Guide

> **Hoved-mål:** Bygge et AI-drevet sample-bibliotek og DAW companion for FL Studio på macOS (og Windows). Verktøyet skal analysere, tagge, organisere og eksportere samples — og til slutt integrere direkte med FL Studio via native macOS-mekanismer eller plugin-APIer.

---

## Innholdsfortegnelse

1. [Prosjektoversikt og arkitektur](#1-prosjektoversikt-og-arkitektur)
2. [Tech stack — Hva vi bruker og Hvorfor](#2-tech-stack--hva-vi-bruker-og-hvorfor)
3. [Tauri vs Electron — Desktop UI valg](#3-tauri-vs-electron--desktop-ui-valg)
4. [FL Studio integrasjon — macOS og Windows](#4-fl-studio-integrasjon--macos-og-windows)
5. [Fase 1 — CLI-prototype ✅](#5-fase-1--cli-prototype-)
6. [Fase 2 — AI-analyse og Web UI 🔄](#6-fase-2--ai-analyse-og-web-ui-)
7. [Fase 3 — Desktop App med Tauri 🔄](#7-fase-3--desktop-app-med-tauri-)
8. [Fase 4 — FL Studio Plugin / VST3 / AU 🔮](#8-fase-4--fl-studio-plugin--vst3--au-)
9. [Fase 5 — Community og sky-deling 🔮](#9-fase-5--community-og-sky-deling-)
10. [Backlog og fremtidige ideer](#10-backlog-og-fremtidige-ideer)
11. [Langsiktig visjon 2026+](#11-langsiktig-visjon-2026)

---

## 1. Prosjektoversikt og arkitektur

```
SampleMind-AI/
├── src/                        # Python backend (analyse, CLI, web)
│   ├── analyzer/
│   │   ├── audio_analysis.py   # librosa-basert BPM, key, mood analyse
│   │   └── classifier.py       # Regelbasert AI: energy, mood, instrument
│   ├── cli/
│   │   ├── analyze.py          # CLI: analysér en fil
│   │   ├── importer.py         # CLI: importer samples til database
│   │   ├── library.py          # CLI: søk og administrer bibliotek
│   │   └── tagger.py           # CLI: manuell tagging
│   └── web/
│       ├── app.py              # Flask web-app (lokal UI)
│       ├── templates/          # HTML Jinja2 templates
│       └── static/             # CSS, JS, waveform-komponenter
├── app/                        # Tauri desktop-app (Rust + Web frontend)
│   ├── src-tauri/
│   │   ├── Cargo.toml          # Rust dependencies
│   │   ├── tauri.conf.json     # Tauri konfigurasjon
│   │   └── src/main.rs         # Rust backend-kode
│   ├── dist/                   # Kompilert frontend (HTML/JS/CSS)
│   └── package.json            # Node/pnpm scripts for Tauri CLI
├── scripts/                    # Hjelpeskript
├── docs/                       # Dokumentasjon
├── requirements.txt            # Python avhengigheter
└── main.py                     # Hoved entry point
```

### Dataflyt (nåværende)

```
WAV-fil → librosa load → BPM + Key + Chroma →
  classifier.py (rule-based AI) → energy + mood + instrument →
    SQLite database → CLI / Web UI / Tauri UI
```

### Dataflyt (fremtidig mål)

```
FL Studio drag-and-drop / sample browser →
  SampleMind Tauri App (native macOS/Windows) →
    Python backend over IPC →
      AI-analyse (librosa + transformers) →
        Database + tags + metadata →
          Tilbake til FL Studio browser via AppleScript / COM / plugin API
```

---

## 2. Tech stack — Hva vi bruker og Hvorfor

| Lag | Teknologi | Begrunnelse |
|-----|-----------|-------------|
| Audio analyse | Python + librosa | Industri-standard for audio ML. Gir BPM, key, spektral features. |
| AI klassifisering | NumPy + regelbasert (nå) → scikit-learn / transformers (fremtid) | Starter enkelt, skalerer til ML. |
| Database | SQLite (via Python) | Fil-basert, ingen server. Perfekt for lokal desktop-app. |
| CLI | Python argparse / click | Raskt å prototype og teste. |
| Web UI (lokal) | Flask + Jinja2 + HTMX | Enkel lokal webserver. HTMX gir reaktivitet uten React/Vue overhead. |
| Desktop app | **Tauri 2** (Rust + Web) | Liten bundle-størrelse, native ytelse, macOS-integrert. Se seksjon 3. |
| Desktop frontend | HTML + CSS + JS (vanilla eller Svelte) | Tauri krever web-frontend. Svelte er lettvektig. |
| macOS-integrasjon | AppleScript / Swift / Rust | For FL Studio-kommunikasjon. Se seksjon 4. |
| Plugin (fremtid) | JUCE (C++) + Python sidecar | VST3/AU plugin som snakker med Python-backend. |

---

## 3. Tauri vs Electron — Desktop UI valg

### Hva er Tauri?

Tauri er et **Rust-basert rammeverk** for å bygge desktop-apper med en web-frontend. I stedet for å pakke inn en hel Chromium-nettleser (som Electron gjør), bruker Tauri operativsystemets **innebygde WebView**:

- **macOS** → `WKWebView` (Safari-motoren)
- **Windows** → `WebView2` (Edge Chromium-basert)
- **Linux** → `WebKitGTK`

```
┌─────────────────────────────────────────┐
│  Electron                               │
│  ┌─────────────────────────────────┐   │
│  │  Chromium (100MB+)              │   │  ← Hele nettleser pakket inn
│  │  + Node.js                      │   │
│  │  + Din app-kode                 │   │
│  └─────────────────────────────────┘   │
│  App-størrelse: ~120-200MB              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Tauri                                  │
│  ┌───────────────┐ ┌─────────────────┐ │
│  │  Rust backend │ │  OS WebView     │ │  ← Bruker system-nettleser
│  │  (din logikk) │ │  (WKWebView)    │ │
│  └───────────────┘ └─────────────────┘ │
│  App-størrelse: ~3-15MB                 │
└─────────────────────────────────────────┘
```

### Sammenligning

| Egenskap | Tauri | Electron |
|----------|-------|----------|
| App-størrelse | ~3–15 MB | ~120–200 MB |
| RAM-bruk | Lavt (Rust backend) | Høyt (Node + Chromium) |
| Ytelse | Veldig rask | Tregere |
| macOS native API | Direkte fra Rust | Via Node native modules |
| Læringsterskel | Høyere (Rust) | Lavere (kun JS) |
| Popularitet | Voksende raskt | Moden, stor community |
| Eks. apper | (ny, få store) | VS Code, Slack, Discord |

### Valget for SampleMind

Vi bruker **Tauri** fordi:
1. Native macOS-integrasjon er enklere fra Rust enn fra Node
2. Lite app-størrelse — viktig for en "lett" DAW-companion
3. Tauri 2 støtter System Tray, native dialogs, og fil-tilgang nativt
4. Rust-ytelse passer bra for lyd-relaterte operasjoner

### Tauri 2 — Nøkkelkonsepter du må lære

#### IPC — Frontend snakker med Rust backend

```rust
// src-tauri/src/main.rs
use tauri::Manager;

#[tauri::command]
fn analyze_sample(file_path: String) -> Result<String, String> {
    // Kall Python-backend via std::process::Command
    // eller kjør Rust-basert analyse direkte
    Ok(format!("Analysert: {}", file_path))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![analyze_sample])
        .run(tauri::generate_context!())
        .expect("error running app");
}
```

```javascript
// Frontend (HTML/JS i dist/)
import { invoke } from '@tauri-apps/api/core';

async function analyzeFile(path) {
  const result = await invoke('analyze_sample', { filePath: path });
  console.log(result);
}
```

#### Events — Rust → Frontend kommunikasjon

```rust
// Rust sender event til frontend
app.emit("analysis-complete", serde_json::json!({
    "bpm": 128.0,
    "key": "C maj",
    "mood": "euphoric"
})).unwrap();
```

```javascript
// Frontend lytter
import { listen } from '@tauri-apps/api/event';

await listen('analysis-complete', (event) => {
  const { bpm, key, mood } = event.payload;
  updateUI(bpm, key, mood);
});
```

#### Native File Dialog (allerede satt opp i prosjektet)

```rust
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
async fn pick_sample_folder(app: tauri::AppHandle) -> Option<String> {
    app.dialog()
        .file()
        .set_title("Velg sample-mappe")
        .pick_folder()
        .await
        .map(|p| p.to_string())
}
```

#### System Tray (allerede konfigurert)

```rust
use tauri::tray::{TrayIconBuilder, TrayIconEvent};

// Kjør SampleMind i bakgrunnen med tray-ikon
// Nyttig for FL Studio workflow — alltid tilgjengelig
TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .on_tray_icon_event(|tray, event| {
        if let TrayIconEvent::Click { .. } = event {
            // Åpne/skjul vinduet
        }
    })
    .build(app)?;
```

---

## 4. FL Studio integrasjon — macOS og Windows

### Integrasjonsstrategier — Fra enkel til avansert

```
Nivå 1: Filsystem-integrasjon (nå mulig)
  └─ Skriv/les filer i FL Studio sin sample-mappe
  └─ Ingen API nødvendig — fungerer i dag

Nivå 2: Clipboard + MIDI (middels)
  └─ Kopier sample-info til clipboard
  └─ MIDI CC-meldinger for parameterstyring

Nivå 3: macOS AppleScript / IPC (avansert)
  └─ Snakk med FL Studio-prosessen
  └─ Automatiser handlinger i appen

Nivå 4: VST3 / AU Plugin (mest integrert)
  └─ SampleMind som plugin inne i FL Studio
  └─ Krever C++ med JUCE framework
```

### Nivå 1 — Filsystem-integrasjon (implementer nå)

FL Studio på macOS lagrer samples her:
```
~/Documents/Image-Line/FL Studio/
├── Projects/               # .flp prosjektfiler
├── Presets/                # Preset-filer for instruments
└── Data/
    └── Projects/
        └── Samples/        # Standard sample-mappe
            └── Packs/      # Sample packs

# macOS user samples (vanlig plassering)
~/Music/
└── SampleMind/             # Vår egen mappe — FL Studio kan peke hit
```

```python
# src/integrations/fl_studio_bridge.py (fremtidig)
import os
import shutil
from pathlib import Path

FL_SAMPLE_DIR = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Data" / "Projects" / "Samples"
SAMPLEMIND_DIR = Path.home() / "Music" / "SampleMind"

def export_to_fl_studio(sample_path: str, category: str, tags: list[str]) -> str:
    """
    Kopier sample til FL Studio sin sample-mappe med riktig mappestruktur.
    FL Studio vil da vise den i sin interne fil-browser.
    """
    dest = FL_SAMPLE_DIR / "SampleMind" / category / Path(sample_path).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_path, dest)

    # Skriv metadata-sidecar fil (XML eller JSON ved siden av WAV-filen)
    _write_metadata_sidecar(dest, tags)
    return str(dest)

def get_fl_studio_projects() -> list[dict]:
    """Finn alle .flp prosjekter — nyttig for prosjekt-kontekst."""
    projects_dir = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Projects"
    return [
        {"name": p.stem, "path": str(p), "modified": p.stat().st_mtime}
        for p in projects_dir.glob("**/*.flp")
    ]
```

### Nivå 2 — macOS AppleScript-integrasjon

AppleScript lar deg automatisere macOS-apper fra Python/Rust. FL Studio støtter begrenset AppleScript, men vi kan bruke det for å:
- Bytte til FL Studio
- Sende tastetrykk (åpne browser, søke)
- Kopiere filstier til clipboard

```python
# src/integrations/applescript_bridge.py
import subprocess

def focus_fl_studio():
    """Bring FL Studio to front."""
    script = 'tell application "FL Studio" to activate'
    subprocess.run(["osascript", "-e", script])

def open_sample_browser_in_fl():
    """Trykk F8 for å åpne sample browser i FL Studio."""
    script = '''
    tell application "System Events"
        tell process "FL Studio"
            key code 98  -- F8
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

def send_sample_path_to_clipboard(path: str):
    """Legg sample-sti i clipboard — brukeren kan paste inn i FL."""
    subprocess.run(["pbcopy"], input=path.encode())
```

```rust
// I Tauri Rust-backend — kalle AppleScript direkte
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

### Nivå 3 — MIDI for FL Studio-kontroll

FL Studio reagerer på MIDI CC-meldinger. Med en virtuell MIDI-port kan SampleMind sende kommandoer:

```python
# Krev: pip install python-rtmidi
# macOS: brew install rtmidi

import rtmidi

def create_virtual_midi_port():
    """Lag en virtuell MIDI-port FL Studio kan koble til."""
    midi_out = rtmidi.MidiOut()
    midi_out.open_virtual_port("SampleMind Control")
    return midi_out

def set_mixer_volume(port, track: int, volume: float):
    """Send CC-melding for å sette mixer-volum."""
    # CC melding: [0xB0 | kanal, CC-nummer, verdi 0-127]
    value = int(volume * 127)
    port.send_message([0xB0, track, value])

def trigger_sample_preview(port):
    """Send Note On for å trigge sample-forhåndsvisning."""
    port.send_message([0x90, 60, 100])  # Note C4, velocity 100
```

### Nivå 4 — VST3 / AU Plugin med JUCE (Langsiktig mål)

JUCE er et C++ rammeverk for å bygge audio plugins. SampleMind Pro-visjonen:

```
┌──────────────────────────────────────────────────┐
│  FL Studio                                        │
│  ┌────────────────────────────────────────────┐  │
│  │  SampleMind AU/VST3 Plugin                 │  │
│  │  ┌────────────┐  ┌──────────────────────┐  │  │
│  │  │  JUCE UI   │  │  Python sidecar      │  │  │
│  │  │  (C++)     │◄─►  (analyse, AI, DB)   │  │  │
│  │  └────────────┘  └──────────────────────┘  │  │
│  │  Kommunikasjon via lokal socket (IPC)       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

```cpp
// Plugin sidecar kommunikasjon (fremtidig)
// JUCE sender JSON til Python-backend via localhost socket

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

### macOS spesifikke hensyn

```
macOS krav for audio-apper:
1. Signing & Notarization — Apple krever signering for distribusjon
   → Tauri har innebygd støtte: tauri.conf.json → bundle.macOS.signingIdentity

2. Hardened Runtime — Påkrevd for notarisering
   → Krever entitlements for mikrofon, fil-tilgang, etc.

3. Sandbox-regler
   → Audio-apper unntatt fra App Sandbox (men må deklarere audio entitlement)

4. AU (Audio Units) vs VST3
   → AU er Apples eget format — best støtte på macOS / Logic
   → VST3 fungerer i FL Studio på macOS
   → Lag BEGGE for maksimal kompatibilitet
```

```xml
<!-- app/src-tauri/Info.plist tillegg for macOS -->
<key>NSMicrophoneUsageDescription</key>
<string>SampleMind needs microphone for live sample capture</string>
<key>com.apple.security.files.user-selected.read-write</key>
<true/>
<key>com.apple.security.assets.music.read-write</key>
<true/>
```

---

## 5. Fase 1 — CLI-prototype ✅

**Status: Fullført**

### Hva som er bygget

| Modul | Fil | Funksjon |
|-------|-----|---------|
| Audio analyse | `src/analyzer/audio_analysis.py` | BPM, key (chroma + tonnetz), mood |
| AI klassifisering | `src/analyzer/classifier.py` | energy, mood, instrument via 8 lydfeatures |
| Import CLI | `src/cli/importer.py` | Importer WAV-filer til database |
| Analyse CLI | `src/cli/analyze.py` | Analyser enkeltfil eller mappe |
| Bibliotek CLI | `src/cli/library.py` | Søk og administrer samples |
| Tagger | `src/cli/tagger.py` | Manuell tagging av samples |

### Kjøre CLI-verktøyene

```bash
# Sett opp miljø
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Analyser en sample
python main.py analyze path/to/sample.wav

# Importer en hel mappe
python main.py import ~/Music/MySamples/

# Søk i biblioteket
python main.py library search --mood dark --instrument kick

# Tag en sample manuelt
python main.py tag sample.wav --tags "trap,heavy,808"
```

### Slik fungerer audio-analysen

```
WAV-fil
  └─ librosa.load() → y (lydbølge), sr (sample rate)
       ├─ BPM: beat_track() → tempo i BPM
       ├─ Key: chroma_cens() → 12 frekvens-bands → høyeste = root note
       │         tonnetz() → harmonisk spenning → major/minor
       └─ Classifier (8 features):
            ├─ rms           → energi/loudness
            ├─ spectral_centroid → lys/mørk klang
            ├─ zero_crossing_rate → støy/perkussiv karakter
            ├─ spectral_flatness  → tone vs hvit støy
            ├─ spectral_rolloff   → høyfrekvent energi
            ├─ onset_strength     → rytmiske anslag
            ├─ low_freq_ratio     → bass-innhold
            └─ duration           → lengde → loop vs one-shot
```

### Gjenstående oppgaver i Fase 1

- [ ] `organizer`-modul: automatisk mappestruktur basert på metadata
  ```
  ~/Music/SampleMind/
  ├── Drums/
  │   ├── Kicks/
  │   │   └── kick_heavy_128bpm_Cmaj.wav
  │   └── Snares/
  └── Bass/
      └── bass_dark_140bpm_Fmin.wav
  ```
- [ ] Testdata-suite med kjente samples og forventede resultater
- [ ] `pytest`-suite for analyzer og classifier

---

## 6. Fase 2 — AI-analyse og Web UI 🔄

**Status: Delvis fullført**

### Hva som mangler

#### 2a. ML-basert klassifisering (erstatning for regelbasert)

Den nåværende `classifier.py` bruker hardkodede terskler. Neste steg er en trent modell:

```python
# Fremtidig: src/analyzer/ml_classifier.py
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

    # Trenings-workflow:
    # 1. Lag labeled dataset (CSV med features + labels)
    # 2. python scripts/train_classifier.py
    # 3. Lagre modell som models/classifier.pkl
```

#### 2b. Web UI forbedringer

```
Nåværende Flask Web UI:
  src/web/app.py → localhost:5000

Mangler:
  [ ] Drag & drop sample-import (Dropzone.js eller native HTML5)
  [ ] Waveform preview (Wavesurfer.js)
  [ ] HTMX for live-oppdatering uten page reload
  [ ] Stemme-basert søk ("finn dark kicks med høy energi")
```

```html
<!-- Waveform preview med Wavesurfer.js -->
<!-- templates/sample_detail.html -->
<div id="waveform"></div>
<button id="play">▶ Spill av</button>

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
<!-- Drag & drop med HTMX -->
<!-- templates/import.html -->
<div id="drop-zone"
     hx-post="/api/import"
     hx-encoding="multipart/form-data"
     hx-trigger="drop"
     hx-target="#results">
  Slipp samples her
</div>
```

---

## 7. Fase 3 — Desktop App med Tauri 🔄

**Status: Tidlig fase — Tauri 2 shell er satt opp**

### Nåværende Tauri-oppsett

```
app/
├── src-tauri/
│   ├── Cargo.toml          # Tauri 2 + dialog + tray-icon
│   ├── tauri.conf.json     # Vindu: 1280x840, system tray
│   └── src/main.rs         # Rust entry point
├── dist/                   # Frontend (ikke bygget ennå)
└── package.json            # Tauri CLI scripts
```

### Bygg og kjør Tauri-appen

```bash
# Krev Rust installert: https://rustup.rs/
# macOS: xcode-select --install

cd app/
pnpm install   # eller: npm install

# Kjør i dev-modus (hot reload)
pnpm tauri dev

# Bygg for distribusjon
pnpm tauri build
# Output: app/src-tauri/target/release/bundle/
#   macOS: SampleMind AI.app + .dmg
#   Windows: .exe + .msi
```

### Plan: Frontend arkitektur for Tauri-appen

Vi skal bygge frontend med **Svelte** (lettvektig, kompilert, rask):

```bash
# Sett opp Svelte i Tauri-prosjektet
cd app/
npm create vite@latest . -- --template svelte
npm install
```

```
app/
├── src/                    # Svelte frontend
│   ├── App.svelte          # Hoved-komponent
│   ├── lib/
│   │   ├── SampleBrowser.svelte   # Liste og filtrer samples
│   │   ├── WaveformPlayer.svelte  # Wavesurfer.js preview
│   │   ├── TagEditor.svelte       # Tag-redigering
│   │   └── ImportDropzone.svelte  # Drag & drop import
│   └── tauri.js            # Tauri API wrappers
├── src-tauri/
└── package.json
```

### Nøkkel Tauri-kommandoer å implementere

```rust
// src-tauri/src/main.rs — kommandoer frontend kan kalle

#[tauri::command]
async fn scan_folder(path: String) -> Result<Vec<SampleInfo>, String> {
    // Kall Python-script eller bruk Rust-basert scanning
    todo!()
}

#[tauri::command]
async fn analyze_sample(path: String) -> Result<AnalysisResult, String> {
    // Spawn Python-prosess: python main.py analyze <path>
    let output = std::process::Command::new("python")
        .args(["main.py", "analyze", &path])
        .output()
        .map_err(|e| e.to_string())?;

    let json_str = String::from_utf8(output.stdout).map_err(|e| e.to_string())?;
    serde_json::from_str(&json_str).map_err(|e| e.to_string())
}

#[tauri::command]
async fn export_to_fl_studio(sample_id: u32) -> Result<String, String> {
    // Kopier fil til FL Studio sample-mappe
    todo!()
}
```

### macOS-spesifikk Tauri-konfigurasjon

```json
// tauri.conf.json — macOS bundle-innstillinger
{
  "bundle": {
    "macOS": {
      "minimumSystemVersion": "12.0",
      "signingIdentity": "Developer ID Application: Ditt Navn",
      "entitlements": "entitlements.plist",
      "exceptionDomain": "",
      "frameworks": []
    },
    "category": "MusicApplication"
  }
}
```

---

## 8. Fase 4 — FL Studio Plugin / VST3 / AU 🔮

**Status: Ikke startet — krever C++ / JUCE-kunnskap**

### Læringsveien mot plugin-utvikling

```
Steg 1: Lær C++ grunnleggende
  └─ Ressurs: "The C++ Programming Language" av Stroustrup
  └─ Fokus: klasser, templates, minnehåndtering, smart pointers

Steg 2: Installer og lær JUCE
  └─ Nedlast: https://juce.com/
  └─ Start med: JUCE Audio Plugin Tutorial
  └─ Bygg et enkelt gain-plugin som øvelse

Steg 3: Lag SampleMind-plugin med Python sidecar
  └─ Plugin UI: JUCE Component (C++)
  └─ Analyse-backend: Python subprocess / socket
  └─ IPC: Unix domain socket (macOS) eller named pipe (Windows)

Steg 4: Signer og distribuer
  └─ macOS: Apple Developer Program ($99/år)
  └─ Notarisering via Xcode eller notarytool
```

### Enkel JUCE Plugin-struktur (referanse)

```cpp
// PluginProcessor.h — Audio Plugin entry point
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class SampleMindProcessor : public juce::AudioProcessor {
public:
    SampleMindProcessor();

    // Disse må implementeres:
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    // Plugin-info
    const juce::String getName() const override { return "SampleMind"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }

    // Analyse-funksjon — kaller Python sidecar
    void analyzeSampleAsync(const juce::File& file);

private:
    // Socket-forbindelse til Python backend
    std::unique_ptr<juce::StreamingSocket> backendSocket;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindProcessor)
};
```

### Python sidecar server (for plugin IPC)

```python
# scripts/plugin_server.py — Kjøres som bakgrunnsprosess av plugin
import socket
import json
from src.analyzer.audio_analysis import analyze_file

HOST = "127.0.0.1"
PORT = 9876

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"SampleMind backend kjører på {HOST}:{PORT}")

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

## 9. Fase 5 — Community og sky-deling 🔮

**Status: Konsept**

### Sample Pack System

```
SampleMind Pack Format (.smpack):
├── manifest.json       # Metadata: navn, BPM, genre, keys, tags
├── samples/
│   ├── kick_128.wav
│   └── bass_dark.wav
└── preview.mp3         # 30-sekunders preview mixdown
```

```json
// manifest.json eksempel
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

### GitHub-basert distribusjon

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

## 10. Backlog og fremtidige ideer

| Idé | Kompleksitet | Verdi | Prioritet |
|-----|-------------|-------|-----------|
| Audio fingerprint matching (unngå duplikater) | Medium | Høy | P1 |
| Automatisk BPM-match til project-tempo | Medium | Høy | P1 |
| Mood wheel UI for sample-søk | Medium | Høy | P2 |
| Smart kompressor/EQ-forslag via AI | Høy | Medium | P2 |
| Stemme-basert søk ("finn dark kicks") | Høy | Høy | P2 |
| AI-assistent som foreslår samples fra skisse | Veldig høy | Veldig høy | P3 |
| Versjonskontroll for sample edits | Medium | Medium | P3 |
| Automatisert tagging av eldre biblioteker | Lav | Høy | P1 |
| Real-time analyse under innspilling | Høy | Medium | P3 |
| Cloud sync av bibliotek og metadata | Høy | Høy | P3 |

### Audio fingerprint-matching (prioritert)

```python
# src/analyzer/fingerprint.py (fremtidig)
import librosa
import numpy as np
from hashlib import sha256

def compute_fingerprint(file_path: str) -> str:
    """
    Lag en akustisk fingeravtrykk for en sample.
    Brukes til å detektere duplikater selv om filnavn er forskjellige.

    Metode: chromagram hash — robust mot volum-endringer og lett EQ.
    """
    y, sr = librosa.load(file_path, duration=10.0)

    # Chroma features er stabile og pitch-uavhengige nok for matching
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    # Kvantiser til 4-bit for robusthet mot små variasjoner
    quantized = (chroma * 15).astype(np.uint8)

    return sha256(quantized.tobytes()).hexdigest()[:16]

def find_duplicates(sample_paths: list[str]) -> list[tuple[str, str]]:
    """Finn alle sample-par som er akustisk identiske."""
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

## 11. Langsiktig visjon 2026+

```
SampleMind AI Produkt-suite:

┌─────────────────────────────────────────────────────────┐
│                  SampleMind Ecosystem                    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  SampleMind  │  │  SampleMind  │  │  SampleMind  │  │
│  │   Desktop    │  │   Plugin     │  │    Cloud     │  │
│  │  (Tauri App) │  │ (VST3 / AU)  │  │  (Web App)   │  │
│  │              │  │              │  │              │  │
│  │  Organiser,  │  │  Direkte i   │  │  Del packs,  │  │
│  │  analyse,    │  │  FL Studio   │  │  backup,     │  │
│  │  søk, export │  │  og DAWer    │  │  kollaborer  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                    Felles backend:                       │
│              Python AI + SQLite + REST API               │
└─────────────────────────────────────────────────────────┘
```

### Milepæler mot SampleMind Pro

| Tidslinje | Mål |
|-----------|-----|
| Q1 2026 | Fullstendig Tauri desktop-app med Svelte UI og Python-integrasjon |
| Q2 2026 | FL Studio filsystem-integrasjon + sample export workflow |
| Q3 2026 | Første JUCE plugin prototype (AU/VST3) |
| Q4 2026 | macOS App Store eller direkte distribusjon med notarisering |
| 2027 | SampleMind Cloud beta — deling, kollaborasjon, AI-mastering |

### Ressurser for å lære

| Tema | Ressurs |
|------|---------|
| Tauri 2 docs | https://v2.tauri.app/start/ |
| Svelte tutorial | https://learn.svelte.dev/ |
| JUCE begynnerguide | https://juce.com/learn/tutorials/ |
| Audio plugin development | "Designing Software Synthesizer Plugins in C++" av Will Pirkle |
| librosa dokumentasjon | https://librosa.org/doc/ |
| Rust begynnerbok | https://doc.rust-lang.org/book/ |
| macOS plugin signing | https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution |

---

*Sist oppdatert: Mars 2026 — Aktiv utvikling pågår*
