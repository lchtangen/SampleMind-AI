# Fase 6 — Desktop-app med Tauri 2 og Svelte 5

> Bygg det fullstendige Svelte 5-frontenden som erstatter `app/dist/index.html`, og utvid
> Rust-backenden med typed kommandoer som kaller Python-CLI via IPC.

---

## Forutsetninger

- Fase 1–5 fullført
- Rust installert: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Node.js 20+ og pnpm: `npm install -g pnpm`
- macOS: `xcode-select --install`

---

## Mål etter denne fasen

- Svelte 5 + Vite satt opp i `app/`
- Full komponent-arkitektur: `SampleTable`, `ImportPanel`, `WaveformPlayer`
- Alle nødvendige Rust `#[tauri::command]`-funksjoner
- System tray fungerer (allerede bygget i Fase 3)
- `pnpm tauri dev` starter appen med HMR

---

## 1. Tre-lags-arkitekturen

```
┌─────────────────────────────────────────────────────┐
│              Svelte 5 (UI-lag)                      │
│  SampleTable ← WaveformPlayer ← ImportPanel         │
│  State: $state rune-basert library store             │
│  IPC: invoke("kommando", { args }) → JSON           │
└──────────────────┬──────────────────────────────────┘
                   │  Tauri invoke() / IPC-kanal
┌──────────────────▼──────────────────────────────────┐
│              Rust (IPC / OS-lag)                    │
│  #[tauri::command] funksjoner                       │
│  Systemdialogs, tray, fil-tilgang                   │
│  Kaller Python som subprocess                        │
└──────────────────┬──────────────────────────────────┘
                   │  std::process::Command
┌──────────────────▼──────────────────────────────────┐
│              Python (analyse / database-lag)        │
│  samplemind import --json                           │
│  samplemind search --json                           │
│  librosa analyse, SQLModel DB                       │
└─────────────────────────────────────────────────────┘
```

---

## 2. Svelte 5 Runes — Grunnkonsepter

Svelte 5 introduserer **Runes** — spesielle `$`-funksjoner som erklærer reaktivitet eksplisitt.
De er en forbedring over Svelte 4 sine implisitte reaktive variabler.

```svelte
<!-- Svelte 4 (gammelt) -->
<script>
  let count = 0;              // Reaktiv pga. kompiler-magi
  $: doubled = count * 2;    // Reaktiv deklarasjon
  $: console.log(count);     // Bieffekt
</script>

<!-- Svelte 5 med Runes (nytt) -->
<script>
  let count = $state(0);                 // $state: eksplisitt reaktiv tilstand
  const doubled = $derived(count * 2);  // $derived: beregnet verdi
  $effect(() => {                        // $effect: bieffekt
    console.log(count);
  });
</script>
```

| Rune | Formål | Erstatter |
|------|--------|-----------|
| `$state(v)` | Reaktiv tilstand | `let v` (implisitt) |
| `$derived(expr)` | Beregnet verdi | `$: derived = expr` |
| `$effect(() => {})` | Bieffekt | `$: statement` |
| `$props()` | Komponent-props | `export let prop` |

---

## 3. Sett opp Svelte 5 + Vite i app/

```bash
# Fra prosjektets rot
$ cd app/

# Initialiser Svelte 5 + Vite + TypeScript
$ pnpm create svelte@latest . --template minimal --types typescript --no-prettier

# Installer Tauri API-pakker
$ pnpm add -D @tauri-apps/api @tauri-apps/cli
$ pnpm add wavesurfer.js

# Oppdater package.json scripts
```

```json
// filename: app/package.json
{
  "name": "samplemind-ai",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^4",
    "@tauri-apps/api": "^2",
    "@tauri-apps/cli": "^2",
    "svelte": "^5",
    "typescript": "^5",
    "vite": "^6"
  },
  "dependencies": {
    "wavesurfer.js": "^7"
  }
}
```

```typescript
// filename: app/vite.config.ts
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],

  // Tauri forventer at frontenden bygges til ../dist (relativt til src-tauri/)
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },

  // Dev-server: Tauri laster dette i stedet for index.html under utvikling
  server: {
    port: 5173,
    strictPort: true,
    host: "localhost",
  },
});
```

---

## 4. Library Store med $state Runes

```typescript
// filename: app/src/lib/stores/library.svelte.ts

import { invoke } from "@tauri-apps/api/core";

// Grensesnitt for sample-data (matcher JSON fra Python CLI)
export interface Sample {
  id: number;
  filename: string;
  path: string;
  bpm: number | null;
  key: string | null;
  mood: string | null;
  energy: string | null;
  instrument: string | null;
  genre: string | null;
  tags: string | null;
}

// $state-basert store — kan brukes i alle Svelte-komponenter
// Dette er en "rune store" — reaktiv uten å trenge Svelte stores
export const library = {
  samples: $state<Sample[]>([]),
  loading: $state(false),
  error: $state<string | null>(null),
  totalCount: $derived(this.samples.length),  // Beregnet fra samples

  // Last inn samples fra Python-backend via Tauri
  async load(filters: SearchFilters = {}) {
    this.loading = true;
    this.error = null;
    try {
      // invoke() kaller Rust-kommandoen "search_samples"
      const result = await invoke<Sample[]>("search_samples", { filters });
      this.samples = result;
    } catch (e) {
      this.error = String(e);
    } finally {
      this.loading = false;
    }
  },
};

export interface SearchFilters {
  query?: string;
  energy?: string;
  instrument?: string;
  bpmMin?: number;
  bpmMax?: number;
  key?: string;
  genre?: string;
}
```

---

## 5. SampleTable-komponenten

```svelte
<!-- filename: app/src/lib/components/SampleTable.svelte -->

<script lang="ts">
  import type { Sample } from "$lib/stores/library.svelte";

  // $props() erstatter "export let" fra Svelte 4
  const { samples, onPlay }: {
    samples: Sample[];
    onPlay: (sample: Sample) => void;
  } = $props();
</script>

<div class="table-wrapper">
  <table>
    <thead>
      <tr>
        <th>Filnavn</th>
        <th>BPM</th>
        <th>Toneart</th>
        <th>Type</th>
        <th>Energi</th>
        <th>Stemning</th>
        <th>Spill av</th>
      </tr>
    </thead>
    <tbody>
      {#each samples as sample (sample.id)}
        <tr class="sample-row">
          <td class="filename">{sample.filename}</td>
          <td class="bpm">{sample.bpm?.toFixed(1) ?? "—"}</td>
          <td>{sample.key ?? "—"}</td>
          <td>
            <span class="badge badge-{sample.instrument}">
              {sample.instrument ?? "—"}
            </span>
          </td>
          <td>
            <span class="badge badge-{sample.energy}">
              {sample.energy ?? "—"}
            </span>
          </td>
          <td>{sample.mood ?? "—"}</td>
          <td>
            <button class="play-btn" onclick={() => onPlay(sample)}>▶</button>
          </td>
        </tr>
      {:else}
        <tr>
          <td colspan="7" class="empty">Ingen samples i biblioteket.</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
```

---

## 6. ImportPanel-komponenten

```svelte
<!-- filename: app/src/lib/components/ImportPanel.svelte -->

<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { library } from "$lib/stores/library.svelte";

  // Lokal tilstand med $state rune
  let importing = $state(false);
  let progress = $state({ current: 0, total: 0, filename: "" });
  let statusMessage = $state("");

  async function pickFolder() {
    // Kall Rust-kommandoen for native mappe-dialog
    const folder = await invoke<string | null>("pick_folder_dialog");
    if (folder) {
      await importFolder(folder);
    }
  }

  async function importFolder(path: string) {
    importing = true;
    statusMessage = "Starter import...";

    try {
      // Kall Rust som kaller Python CLI med --json
      const result = await invoke<{ imported: number; samples: any[] }>(
        "import_folder",
        { path }
      );
      statusMessage = `Ferdig! Importerte ${result.imported} samples.`;
      await library.load(); // Oppdater tabellen
    } catch (e) {
      statusMessage = `Feil: ${e}`;
    } finally {
      importing = false;
    }
  }
</script>

<div class="import-panel">
  <h2>Importer samples</h2>

  <button onclick={pickFolder} disabled={importing} class="btn-primary">
    {importing ? "Importerer..." : "Velg mappe..."}
  </button>

  {#if importing}
    <!-- Fremgangslinje -->
    <div class="progress-bar-wrapper">
      <div
        class="progress-bar"
        style="width: {progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%"
      ></div>
    </div>
    <p class="progress-text">{progress.filename}</p>
  {/if}

  {#if statusMessage}
    <p class="status-message">{statusMessage}</p>
  {/if}
</div>
```

---

## 7. WaveformPlayer-komponenten

```svelte
<!-- filename: app/src/lib/components/WaveformPlayer.svelte -->

<script lang="ts">
  import { onDestroy } from "svelte";
  import WaveSurfer from "wavesurfer.js";
  import type { Sample } from "$lib/stores/library.svelte";

  const { sample }: { sample: Sample | null } = $props();

  let waveContainer: HTMLDivElement;
  let ws: WaveSurfer | null = null;
  let playing = $state(false);

  // $effect kjører når sample-prop endres — laster ny waveform
  $effect(() => {
    if (!sample || !waveContainer) return;

    // Ødelegg forrige instans
    ws?.destroy();

    // Bygg URL til Tauri's asset protocol (eller Flask-backend)
    const audioUrl = `http://localhost:5000/audio/${sample.id}`;

    ws = WaveSurfer.create({
      container: waveContainer,
      waveColor: "#6366f1",
      progressColor: "#4f46e5",
      height: 60,
      barWidth: 2,
      url: audioUrl,
    });

    ws.on("finish", () => { playing = false; });
  });

  function togglePlay() {
    if (!ws) return;
    ws.playPause();
    playing = !playing;
  }

  // Rydd opp Wavesurfer når komponenten fjernes
  onDestroy(() => ws?.destroy());
</script>

{#if sample}
  <div class="waveform-player">
    <p class="waveform-filename">{sample.filename}</p>
    <div bind:this={waveContainer} class="waveform-container"></div>
    <button onclick={togglePlay} class="play-button">
      {playing ? "⏸ Pause" : "▶ Spill av"}
    </button>
    {#if sample.bpm}
      <span class="bpm-badge">{sample.bpm.toFixed(1)} BPM</span>
    {/if}
    {#if sample.key}
      <span class="key-badge">{sample.key}</span>
    {/if}
  </div>
{/if}
```

---

## 8. Rust-kommandoer (utvidet main.rs)

```rust
// filename: app/src-tauri/src/main.rs

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::sync::{Arc, Mutex};
use tauri::{Manager, State};
use tauri::tray::{TrayIconBuilder, TrayIconEvent};
use tauri_plugin_dialog::DialogExt;
use serde::{Deserialize, Serialize};

// ── Delte tilstandstyper ─────────────────────────────────────────────────────

#[derive(Default)]
struct AppState {
    flask_port: u16,
}

// ── Datatyper for IPC ────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SampleJson {
    pub id: Option<i64>,
    pub filename: String,
    pub path: String,
    pub bpm: Option<f64>,
    pub key: Option<String>,
    pub mood: Option<String>,
    pub energy: Option<String>,
    pub instrument: Option<String>,
    pub genre: Option<String>,
    pub tags: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ImportResult {
    pub imported: usize,
    pub samples: Vec<SampleJson>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SearchFilters {
    pub query: Option<String>,
    pub energy: Option<String>,
    pub instrument: Option<String>,
    pub bpm_min: Option<f64>,
    pub bpm_max: Option<f64>,
    pub key: Option<String>,
    pub genre: Option<String>,
}

// ── Tauri-kommandoer ─────────────────────────────────────────────────────────

/// Kall Python CLI for å importere en mappe. Returnerer JSON-resultat.
#[tauri::command]
async fn import_folder(path: String) -> Result<ImportResult, String> {
    let output = Command::new("samplemind")
        .args(["import", &path, "--json"])
        .output()
        .map_err(|e| format!("Kunne ikke starte samplemind: {e}"))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Ugyldig JSON: {e}"))
}

/// Søk i sample-biblioteket via Python CLI
#[tauri::command]
async fn search_samples(filters: SearchFilters) -> Result<Vec<SampleJson>, String> {
    let mut args = vec!["search", "--json"];
    let query_str;
    let energy_str;

    if let Some(ref q) = filters.query { query_str = q.clone(); args.push(&query_str); }
    if let Some(ref e) = filters.energy {
        args.push("--energy");
        energy_str = e.clone();
        args.push(&energy_str);
    }
    // ... tilsvarende for de andre filtrene

    let output = Command::new("samplemind")
        .args(&args)
        .output()
        .map_err(|e| format!("samplemind feilet: {e}"))?;

    serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Ugyldig JSON: {e}"))
}

/// Åpne native mappe-dialog
#[tauri::command]
async fn pick_folder_dialog(app: tauri::AppHandle) -> Option<String> {
    app.dialog()
        .file()
        .set_title("Velg sample-mappe")
        .pick_folder()
        .await
        .map(|p| p.to_string())
}

/// Skjul/vis hoved-vinduet
#[tauri::command]
fn toggle_window(app: tauri::AppHandle) {
    let window = app.get_webview_window("main").unwrap();
    if window.is_visible().unwrap_or(false) {
        window.hide().unwrap();
    } else {
        window.show().unwrap();
        window.set_focus().unwrap();
    }
}

// ── Hoved entry point ────────────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(Arc::new(Mutex::new(AppState { flask_port: 5000 })))
        .invoke_handler(tauri::generate_handler![
            import_folder,
            search_samples,
            pick_folder_dialog,
            toggle_window,
        ])
        .setup(|app| {
            // System tray
            TrayIconBuilder::new()
                .tooltip("SampleMind AI")
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { .. } = event {
                        let app = tray.app_handle();
                        let window = app.get_webview_window("main").unwrap();
                        if window.is_visible().unwrap_or(false) {
                            window.hide().unwrap();
                        } else {
                            window.show().unwrap();
                        }
                    }
                })
                .build(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Feil ved kjøring av app");
}
```

---

## 9. Oppdatert tauri.conf.json

```json
// filename: app/src-tauri/tauri.conf.json
{
  "productName": "SampleMind AI",
  "version": "0.1.0",
  "identifier": "com.samplemind.ai",

  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build"
  },

  "app": {
    "withGlobalTauri": false,

    "windows": [
      {
        "label": "main",
        "title": "SampleMind AI",
        "width": 1280,
        "height": 840,
        "minWidth": 960,
        "minHeight": 600,
        "center": true,
        "resizable": true,
        "decorations": true,
        "visible": false
      }
    ],

    "security": {
      "csp": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self' http://localhost:5000"
    }
  },

  "bundle": {
    "active": false,
    "targets": "all",
    "icon": ["icons/icon.png"],
    "macOS": {
      "minimumSystemVersion": "12.0"
    }
  }
}
```

---

## 10. Utvikling og HMR

```bash
# Start Tauri i dev-modus (HMR = Hot Module Replacement = live-reload)
$ cd app/
$ pnpm tauri:dev

# Dette gjør følgende automatisk:
# 1. Starter Vite dev-server på localhost:5173
# 2. Kompilerer Rust-backend
# 3. Åpner app-vinduet som laster fra Vite

# Bygg for produksjon
$ pnpm tauri:build
# Output: app/src-tauri/target/release/bundle/
#   macOS: SampleMind AI.app + SampleMind AI.dmg
```

---

## Migrasjonsnotater

- `app/dist/index.html` (gammel placeholder) erstattes av Vite-output
- `app/package.json` oppdateres med Svelte 5 og Vite
- Eksisterende Rust-kode i `main.rs` beholdes og utvides

---

## Testsjekkliste

```bash
# Bekreft at Rust kompilerer
$ cd app/ && cargo check --manifest-path src-tauri/Cargo.toml

# Start dev-modus
$ pnpm tauri:dev

# Test i appen:
# - Klikk "Velg mappe" → native dialog åpnes
# - Dra en WAV-fil til vinduet
# - Søk i biblioteket
# - Spill av en sample

# Bekreft at tray-ikonet fungerer (minimerer til tray)
```

---

## Feilsøking

**Feil: `samplemind: command not found` fra Rust**
```bash
# Bekreft at samplemind er installert og i PATH
$ which samplemind
# Eller bruk full sti i Rust:
let output = Command::new("/home/bruker/.local/bin/samplemind")
```

**Feil: Svelte 5 rune utenfor .svelte-fil**
```
$state og andre runes fungerer kun i .svelte-filer eller .svelte.ts-filer.
Store-filer bruker suffiksen .svelte.ts (ikke .ts).
```

**Feil: CORS-feil ved lasting av audio fra Flask**
```python
# Legg til CORS i Flask-appen:
from flask_cors import CORS
CORS(app, origins=["tauri://localhost", "http://localhost:5173"])
```
