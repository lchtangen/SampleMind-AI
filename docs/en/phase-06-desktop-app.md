# Phase 6 — Desktop App with Tauri 2 and Svelte 5

> Build the complete Svelte 5 frontend that replaces `app/dist/index.html`, and extend the
> Rust backend with typed commands that call the Python CLI via IPC.

---

## Prerequisites

- Phases 1–5 complete
- Rust installed: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Node.js 20+ and pnpm: `npm install -g pnpm`
- macOS: `xcode-select --install`

---

## Goal State

- Svelte 5 + Vite set up in `app/`
- Full component architecture: `SampleTable`, `ImportPanel`, `WaveformPlayer`
- All necessary Rust `#[tauri::command]` functions
- System tray working (already built in earlier phases)
- `pnpm tauri dev` starts the app with HMR

---

## 1. The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│              Svelte 5 (UI layer)                    │
│  SampleTable ← WaveformPlayer ← ImportPanel         │
│  State: $state rune-based library store             │
│  IPC: invoke("command", { args }) → JSON            │
└──────────────────┬──────────────────────────────────┘
                   │  Tauri invoke() / IPC channel
┌──────────────────▼──────────────────────────────────┐
│              Rust (IPC / OS layer)                  │
│  #[tauri::command] functions                        │
│  System dialogs, tray, file access                  │
│  Calls Python as subprocess                         │
└──────────────────┬──────────────────────────────────┘
                   │  std::process::Command
┌──────────────────▼──────────────────────────────────┐
│              Python (analysis / database layer)     │
│  samplemind import --json                           │
│  samplemind search --json                           │
│  librosa analysis, SQLModel DB                      │
└─────────────────────────────────────────────────────┘
```

---

## 2. Svelte 5 Runes — Core Concepts

Svelte 5 introduces **Runes** — special `$` functions that declare reactivity explicitly.
They are an improvement over Svelte 4's implicit reactive variables.

```svelte
<!-- Svelte 4 (old) -->
<script>
  let count = 0;              // Reactive via compiler magic
  $: doubled = count * 2;    // Reactive declaration
  $: console.log(count);     // Side effect
</script>

<!-- Svelte 5 with Runes (new) -->
<script>
  let count = $state(0);                 // $state: explicit reactive state
  const doubled = $derived(count * 2);  // $derived: computed value
  $effect(() => {                        // $effect: side effect
    console.log(count);
  });
</script>
```

| Rune | Purpose | Replaces |
|------|---------|---------|
| `$state(v)` | Reactive state | `let v` (implicit) |
| `$derived(expr)` | Computed value | `$: derived = expr` |
| `$effect(() => {})` | Side effect | `$: statement` |
| `$props()` | Component props | `export let prop` |

---

## 3. Set Up Svelte 5 + Vite in app/

```bash
# From project root
$ cd app/

# Initialise Svelte 5 + Vite + TypeScript
$ pnpm create svelte@latest . --template minimal --types typescript --no-prettier

# Install Tauri API packages
$ pnpm add -D @tauri-apps/api @tauri-apps/cli
$ pnpm add wavesurfer.js
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

  // Tauri expects frontend built to ../dist (relative to src-tauri/)
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },

  // Dev server: Tauri loads this instead of index.html during development
  server: {
    port: 5173,
    strictPort: true,
    host: "localhost",
  },
});
```

---

## 4. Library Store with $state Runes

```typescript
// filename: app/src/lib/stores/library.svelte.ts

import { invoke } from "@tauri-apps/api/core";

// Interface for sample data (matches JSON from Python CLI)
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

// $state-based store — usable in all Svelte components
export const library = {
  samples: $state<Sample[]>([]),
  loading: $state(false),
  error: $state<string | null>(null),

  // Load samples from Python backend via Tauri
  async load(filters: SearchFilters = {}) {
    this.loading = true;
    this.error = null;
    try {
      // invoke() calls the Rust command "search_samples"
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

## 5. The SampleTable Component

```svelte
<!-- filename: app/src/lib/components/SampleTable.svelte -->

<script lang="ts">
  import type { Sample } from "$lib/stores/library.svelte";

  // $props() replaces "export let" from Svelte 4
  const { samples, onPlay }: {
    samples: Sample[];
    onPlay: (sample: Sample) => void;
  } = $props();
</script>

<div class="table-wrapper">
  <table>
    <thead>
      <tr>
        <th>Filename</th>
        <th>BPM</th>
        <th>Key</th>
        <th>Type</th>
        <th>Energy</th>
        <th>Mood</th>
        <th>Play</th>
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
          <td colspan="7" class="empty">No samples in library.</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
```

---

## 6. The ImportPanel Component

```svelte
<!-- filename: app/src/lib/components/ImportPanel.svelte -->

<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { library } from "$lib/stores/library.svelte";

  // Local state with $state rune
  let importing = $state(false);
  let progress = $state({ current: 0, total: 0, filename: "" });
  let statusMessage = $state("");

  async function pickFolder() {
    // Call Rust command for native folder dialog
    const folder = await invoke<string | null>("pick_folder_dialog");
    if (folder) {
      await importFolder(folder);
    }
  }

  async function importFolder(path: string) {
    importing = true;
    statusMessage = "Starting import...";

    try {
      // Call Rust which calls Python CLI with --json
      const result = await invoke<{ imported: number; samples: any[] }>(
        "import_folder",
        { path }
      );
      statusMessage = `Done! Imported ${result.imported} samples.`;
      await library.load(); // Refresh the table
    } catch (e) {
      statusMessage = `Error: ${e}`;
    } finally {
      importing = false;
    }
  }
</script>

<div class="import-panel">
  <h2>Import Samples</h2>

  <button onclick={pickFolder} disabled={importing} class="btn-primary">
    {importing ? "Importing..." : "Choose folder..."}
  </button>

  {#if importing}
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

## 7. The WaveformPlayer Component

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

  // $effect runs when sample prop changes — loads new waveform
  $effect(() => {
    if (!sample || !waveContainer) return;

    ws?.destroy();

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

  onDestroy(() => ws?.destroy());
</script>

{#if sample}
  <div class="waveform-player">
    <p class="waveform-filename">{sample.filename}</p>
    <div bind:this={waveContainer} class="waveform-container"></div>
    <button onclick={togglePlay} class="play-button">
      {playing ? "⏸ Pause" : "▶ Play"}
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

## 8. Rust Commands (extended main.rs)

```rust
// filename: app/src-tauri/src/main.rs

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::sync::{Arc, Mutex};
use tauri::Manager;
use tauri::tray::{TrayIconBuilder, TrayIconEvent};
use tauri_plugin_dialog::DialogExt;
use serde::{Deserialize, Serialize};

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

/// Call Python CLI to import a folder. Returns JSON result.
#[tauri::command]
async fn import_folder(path: String) -> Result<ImportResult, String> {
    let output = Command::new("samplemind")
        .args(["import", &path, "--json"])
        .output()
        .map_err(|e| format!("Could not start samplemind: {e}"))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Invalid JSON: {e}"))
}

/// Search the sample library via Python CLI
#[tauri::command]
async fn search_samples(filters: SearchFilters) -> Result<Vec<SampleJson>, String> {
    let mut args = vec!["search".to_string(), "--json".to_string()];

    if let Some(ref q) = filters.query {
        args.push(q.clone());
    }
    if let Some(ref e) = filters.energy {
        args.push("--energy".to_string());
        args.push(e.clone());
    }
    if let Some(ref i) = filters.instrument {
        args.push("--instrument".to_string());
        args.push(i.clone());
    }

    let output = Command::new("samplemind")
        .args(&args)
        .output()
        .map_err(|e| format!("samplemind failed: {e}"))?;

    serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Invalid JSON: {e}"))
}

/// Open native folder dialog
#[tauri::command]
async fn pick_folder_dialog(app: tauri::AppHandle) -> Option<String> {
    app.dialog()
        .file()
        .set_title("Choose sample folder")
        .pick_folder()
        .await
        .map(|p| p.to_string())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            import_folder,
            search_samples,
            pick_folder_dialog,
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
        .expect("Error running app");
}
```

---

## 9. Development and HMR

```bash
# Start Tauri in dev mode (HMR = Hot Module Replacement = live reload)
$ cd app/
$ pnpm tauri:dev

# This automatically:
# 1. Starts Vite dev server on localhost:5173
# 2. Compiles Rust backend
# 3. Opens app window loading from Vite

# Build for production
$ pnpm tauri:build
# Output: app/src-tauri/target/release/bundle/
#   macOS: SampleMind AI.app + SampleMind AI.dmg
#   Windows: .exe + .msi
```

---

## Migration Notes

- `app/dist/index.html` (old placeholder) is replaced by Vite build output
- `app/package.json` is updated with Svelte 5 and Vite
- Existing Rust code in `main.rs` is kept and extended

---

## Testing Checklist

```bash
# Confirm Rust compiles
$ cd app/ && cargo check --manifest-path src-tauri/Cargo.toml

# Start dev mode
$ pnpm tauri:dev

# Test in the app:
# - Click "Choose folder" → native dialog opens
# - Drag a WAV file to the window
# - Search the library
# - Play a sample

# Confirm the tray icon works (minimises to tray)
```

---

## Troubleshooting

**Error: `samplemind: command not found` from Rust**
```bash
# Confirm samplemind is installed and in PATH
$ which samplemind
# Or use full path in Rust:
let output = Command::new("/home/user/.local/bin/samplemind")
```

**Error: Svelte 5 rune outside .svelte file**
```
$state and other runes only work in .svelte files or .svelte.ts files.
Store files use the .svelte.ts suffix (not .ts).
```

**Error: CORS error loading audio from Flask**
```python
# Add CORS to the Flask app:
from flask_cors import CORS
CORS(app, origins=["tauri://localhost", "http://localhost:5173"])
```
