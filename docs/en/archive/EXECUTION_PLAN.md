# SampleMind AI — Systematic Execution Plan for Claude Code

**Created:** 2026-03-25  
**Current Status:** Phase 4 (70% complete)  
**Target:** Complete Phases 4-10 systematically

---

## Execution Priority Matrix

| Phase | Priority | Blockers | Estimated Effort | Target Completion |
|-------|----------|----------|------------------|-------------------|
| **Phase 4** | P0 (Critical) | None | 2-3 days | Week 1 |
| **Phase 5** | P1 (High) | Phase 4 | 3-4 days | Week 2 |
| **Phase 6** | P1 (High) | Phase 5 | 5-7 days | Week 3-4 |
| **Phase 7** | P2 (Medium) | Phase 6 | 4-5 days | Week 5 |
| **Phase 8** | P2 (Medium) | Phase 7 | 7-10 days | Week 6-7 |
| **Phase 9** | P3 (Low) | Phase 4 | 3-4 days | Week 8 |
| **Phase 10** | P0 (Critical) | Phases 6-9 | 5-7 days | Week 9-10 |

---

## Phase 4: CLI Modernization (CURRENT) — 70% Complete

**Goal:** Complete CLI with parallel processing, FTS5 search, and performance optimization

### Task 4.1: Parallel Import with Workers ⏳
**Files to modify:**
- `src/samplemind/cli/commands/import_.py`

**Implementation:**
```python
# Add --workers flag to import command
@app.command()
def import_(
    source: Path,
    workers: int = typer.Option(0, help="Worker processes (0=auto)"),
    json: bool = False
):
    from samplemind.analyzer.batch import analyze_batch
    # Use analyze_batch() with ProcessPoolExecutor
```

**Acceptance criteria:**
- [ ] `samplemind import ~/Music/Samples --workers 4` works
- [ ] `--workers 0` auto-detects CPU count
- [ ] Progress bar shows completion rate
- [ ] `--json` output includes timing stats

---

### Task 4.2: FTS5 Full-Text Search 🔴 CRITICAL
**Files to create/modify:**
- `src/samplemind/data/fts.py` (new)
- `migrations/versions/0003_add_fts5_table.py` (new)
- `src/samplemind/data/repositories/sample_repository.py` (modify)

**Implementation:**
```python
# migrations/versions/0003_add_fts5_table.py
def upgrade():
    op.execute("""
        CREATE VIRTUAL TABLE samples_fts USING fts5(
            filename, tags, genre, mood, instrument,
            content='samples', content_rowid='id'
        )
    """)
    op.execute("""
        CREATE TRIGGER samples_ai AFTER INSERT ON samples BEGIN
            INSERT INTO samples_fts(rowid, filename, tags, genre, mood, instrument)
            VALUES (new.id, new.filename, new.tags, new.genre, new.mood, new.instrument);
        END
    """)

# src/samplemind/data/fts.py
def fts_search(query: str, limit: int = 50) -> list[int]:
    """Return sample IDs matching FTS5 query."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT rowid FROM samples_fts WHERE samples_fts MATCH ? LIMIT ?",
        (query, limit)
    ).fetchall()
    return [r[0] for r in rows]
```

**Acceptance criteria:**
- [ ] Migration `0003` applies cleanly
- [ ] `samplemind search "dark kick"` uses FTS5
- [ ] Search returns results in <50ms
- [ ] Triggers keep FTS5 in sync on insert/update

---

### Task 4.3: Performance Optimization 🔴 CRITICAL
**Files to modify:**
- `src/samplemind/analyzer/audio_analysis.py`

**Optimizations:**
1. Cache librosa FFT results between feature extractions
2. Reduce default `sr=22050` (from 44100) for faster processing
3. Skip BPM detection for files <1s (not meaningful)
4. Add `--skip-analysis` flag to re-import without re-analyzing

**Target:** <500ms per file (currently ~800ms)

**Acceptance criteria:**
- [ ] Single file analysis <500ms (measured with `time`)
- [ ] Batch of 100 files <30s with 4 workers
- [ ] No accuracy regression in classifier outputs

---

### Task 4.4: Shell Completion
**Files to modify:**
- `src/samplemind/cli/app.py`

**Implementation:**
```python
# Already supported by Typer — just document it
# User runs: samplemind --install-completion
# Adds to ~/.bashrc or ~/.zshrc automatically
```

**Acceptance criteria:**
- [ ] `samplemind --install-completion` works
- [ ] Tab completion works for commands
- [ ] Tab completion works for `--energy`, `--mood`, `--instrument` values

---

## Phase 5: Web UI Improvements — 0% Complete

**Goal:** Modern Flask app with HTMX, SSE, and waveform preview

### Task 5.1: Application Factory Pattern 🔴 CRITICAL
**Files to modify:**
- `src/samplemind/web/app.py` (refactor)
- `src/samplemind/cli/commands/serve.py` (update)

**Implementation:**
```python
# src/samplemind/web/app.py
def create_app(config: dict = None) -> Flask:
    app = Flask(__name__)
    app.config.setdefault("SECRET_KEY", "samplemind-dev-key")
    if config:
        app.config.update(config)
    
    from samplemind.web.blueprints.library import library_bp
    from samplemind.web.blueprints.import_ import import_bp
    app.register_blueprint(library_bp)
    app.register_blueprint(import_bp)
    return app
```

**Acceptance criteria:**
- [ ] `create_app()` factory works
- [ ] Blueprints registered correctly
- [ ] Tests use `app.test_client()`
- [ ] `samplemind serve` still works

---

### Task 5.2: HTMX Live Search
**Files to create/modify:**
- `src/samplemind/web/templates/library.html` (modify)
- `src/samplemind/web/blueprints/library.py` (add route)

**Implementation:**
```html
<!-- library.html -->
<input type="search" name="q" 
       hx-get="/library/search" 
       hx-trigger="keyup changed delay:300ms" 
       hx-target="#results">

<div id="results">
    <!-- HTMX replaces this with search results -->
</div>
```

```python
# library.py
@library_bp.route("/library/search")
def search():
    query = request.args.get("q", "")
    samples = SampleRepository.search(query=query)
    return render_template("_results.html", samples=samples)
```

**Acceptance criteria:**
- [ ] Search updates without page reload
- [ ] 300ms debounce prevents excessive queries
- [ ] Results render in <100ms

---

### Task 5.3: SSE Import Progress
**Files to create/modify:**
- `src/samplemind/web/blueprints/import_.py` (add SSE route)
- `src/samplemind/web/templates/import.html` (add EventSource)

**Implementation:**
```python
# import_.py
@import_bp.route("/import/stream")
def import_stream():
    def generate():
        # Yield progress events
        for i, result in enumerate(analyze_batch(files, progress_cb=...)):
            yield f"data: {json.dumps({'progress': i, 'total': len(files)})}\n\n"
    return Response(generate(), mimetype="text/event-stream")
```

**Acceptance criteria:**
- [ ] Progress bar updates in real-time
- [ ] Shows current file being analyzed
- [ ] Completes with success/error summary

---

### Task 5.4: Waveform Preview (wavesurfer.js)
**Files to create/modify:**
- `src/samplemind/web/static/js/waveform.js` (new)
- `src/samplemind/web/templates/library.html` (add waveform div)

**Implementation:**
```javascript
// waveform.js
import WaveSurfer from 'wavesurfer.js';

function loadWaveform(sampleId) {
    const wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#4a9eff',
        progressColor: '#1e3a8a'
    });
    wavesurfer.load(`/audio/${sampleId}`);
}
```

**Acceptance criteria:**
- [ ] Waveform renders on sample click
- [ ] Play/pause controls work
- [ ] Loads in <500ms for typical samples

---

## Phase 6: Desktop App (Tauri + Svelte 5) — 30% Complete

**Goal:** Replace Flask WebView with native Svelte 5 frontend

### Task 6.1: Svelte 5 Project Setup 🔴 CRITICAL
**Files to create:**
- `app/src/App.svelte` (new)
- `app/src/lib/stores/library.svelte.ts` (new)
- `app/src/lib/components/SampleTable.svelte` (new)

**Implementation:**
```bash
cd app/
pnpm create svelte@latest . --template minimal --types typescript
pnpm add @tauri-apps/api wavesurfer.js
```

**Acceptance criteria:**
- [ ] `pnpm tauri dev` starts app with Svelte UI
- [ ] No Flask dependency in dev mode
- [ ] HMR (hot module reload) works

---

### Task 6.2: Tauri IPC Commands
**Files to modify:**
- `app/src-tauri/src/main.rs` (add commands)

**Implementation:**
```rust
#[tauri::command]
async fn import_folder(path: String) -> Result<String, String> {
    let output = Command::new("samplemind")
        .args(["import", &path, "--json"])
        .output()
        .map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

#[tauri::command]
async fn search_samples(query: String) -> Result<String, String> {
    let output = Command::new("samplemind")
        .args(["search", "--query", &query, "--json"])
        .output()
        .map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
```

**Acceptance criteria:**
- [ ] `import_folder()` calls Python CLI
- [ ] `search_samples()` returns JSON
- [ ] Error handling works (Python not found, etc.)

---

### Task 6.3: Svelte Components
**Files to create:**
- `app/src/lib/components/SampleTable.svelte`
- `app/src/lib/components/ImportPanel.svelte`
- `app/src/lib/components/WaveformPlayer.svelte`
- `app/src/lib/components/SearchBar.svelte`

**Implementation:**
```svelte
<!-- SampleTable.svelte -->
<script lang="ts">
    import { invoke } from '@tauri-apps/api/core';
    let samples = $state<Sample[]>([]);
    
    async function loadSamples() {
        const json = await invoke('search_samples', { query: '' });
        samples = JSON.parse(json);
    }
</script>

<table>
    {#each samples as sample}
        <tr>
            <td>{sample.filename}</td>
            <td>{sample.bpm}</td>
            <td>{sample.key}</td>
        </tr>
    {/each}
</table>
```

**Acceptance criteria:**
- [ ] SampleTable displays library
- [ ] ImportPanel shows progress
- [ ] WaveformPlayer renders audio
- [ ] SearchBar filters in real-time

---

### Task 6.4: Production Builds
**Files to modify:**
- `app/src-tauri/tauri.conf.json` (bundle config)

**Implementation:**
```bash
# macOS Universal Binary
pnpm tauri build --target universal-apple-darwin

# Windows
pnpm tauri build --target x86_64-pc-windows-msvc

# Linux
pnpm tauri build --target x86_64-unknown-linux-gnu
```

**Acceptance criteria:**
- [ ] macOS .dmg builds successfully
- [ ] Windows .msi builds successfully
- [ ] App size <20 MB
- [ ] Cold start <2s

---

## Phase 7: FL Studio Integration — 0% Complete

**Goal:** Export samples to FL Studio with metadata

### Task 7.1: Filesystem Export
**Files to create:**
- `src/samplemind/integrations/fl_studio.py` (new)
- `src/samplemind/cli/commands/export.py` (modify)

**Implementation:**
```python
# fl_studio.py
FL_SAMPLE_DIR = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Data" / "Projects" / "Samples"

def export_to_fl_studio(sample_id: int, category: str) -> Path:
    sample = SampleRepository.get_by_id(sample_id)
    dest = FL_SAMPLE_DIR / "SampleMind" / category / sample.filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample.path, dest)
    return dest
```

**Acceptance criteria:**
- [ ] `samplemind export --fl-studio` copies to FL folder
- [ ] Organizes by instrument/mood
- [ ] Preserves metadata in sidecar JSON

---

### Task 7.2: AppleScript Automation (macOS)
**Files to create:**
- `src/samplemind/integrations/applescript.py` (new)

**Implementation:**
```python
def focus_fl_studio():
    script = 'tell application "FL Studio" to activate'
    subprocess.run(["osascript", "-e", script])

def open_sample_browser():
    script = '''
    tell application "System Events"
        tell process "FL Studio"
            key code 98  -- F8
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
```

**Acceptance criteria:**
- [ ] `focus_fl_studio()` brings FL to front
- [ ] `open_sample_browser()` opens browser
- [ ] Works on macOS 12+

---

## Phase 8: VST3/AU Plugin (JUCE 8) — 0% Complete

**Goal:** Native plugin for FL Studio

### Task 8.1: JUCE Project Setup
**Files to create:**
- `plugin/CMakeLists.txt` (new)
- `plugin/src/PluginProcessor.h` (new)
- `plugin/src/PluginProcessor.cpp` (new)
- `plugin/src/PluginEditor.h` (new)
- `plugin/src/PluginEditor.cpp` (new)

**Implementation:**
```bash
cd plugin/
git clone https://github.com/juce-framework/JUCE.git
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

**Acceptance criteria:**
- [ ] JUCE project compiles
- [ ] VST3 + AU targets build
- [ ] Plugin loads in FL Studio

---

### Task 8.2: Python Sidecar Server
**Files to create:**
- `src/samplemind/sidecar/server.py` (new)

**Implementation:**
```python
# server.py
import socket, json, struct

def start_server():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind("/tmp/samplemind.sock")
    sock.listen(1)
    
    while True:
        conn, _ = sock.accept()
        length = struct.unpack(">I", conn.recv(4))[0]
        data = json.loads(conn.recv(length))
        
        if data["action"] == "search":
            results = SampleRepository.search(query=data["query"])
            response = json.dumps([r.dict() for r in results])
        
        conn.send(struct.pack(">I", len(response)))
        conn.send(response.encode())
```

**Acceptance criteria:**
- [ ] Sidecar starts on plugin load
- [ ] Socket communication works
- [ ] Search returns results <100ms

---

## Phase 9: Sample Packs — 0% Complete

**Goal:** Export/import .smpack bundles

### Task 9.1: Pack Format
**Files to create:**
- `src/samplemind/packs/manifest.py` (new)
- `src/samplemind/packs/pack.py` (new)

**Implementation:**
```python
# manifest.py
class PackManifest(BaseModel):
    name: str
    version: str
    samples: list[SampleEntry]
    
class SampleEntry(BaseModel):
    filename: str
    sha256: str
    bpm: float | None
    key: str | None
```

**Acceptance criteria:**
- [ ] `samplemind pack create` builds .smpack
- [ ] `samplemind pack import` extracts and imports
- [ ] SHA-256 verification works

---

## Phase 10: Production & Release — 0% Complete

**Goal:** Signed, notarized, production-ready builds

### Task 10.1: macOS Signing
**Files to create:**
- `scripts/sign-macos.sh` (new)
- `.github/workflows/release.yml` (new)

**Implementation:**
```bash
# sign-macos.sh
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Your Name" \
    --options runtime \
    SampleMind.app

xcrun notarytool submit SampleMind.dmg \
    --apple-id "your@email.com" \
    --password "@keychain:AC_PASSWORD" \
    --team-id "TEAMID"
```

**Acceptance criteria:**
- [ ] App is signed with Developer ID
- [ ] Notarization succeeds
- [ ] Gatekeeper allows app to run

---

## Execution Order Summary

### Week 1: Complete Phase 4
1. Task 4.1: Parallel import
2. Task 4.2: FTS5 search
3. Task 4.3: Performance optimization
4. Task 4.4: Shell completion

### Week 2: Complete Phase 5
1. Task 5.1: Application factory
2. Task 5.2: HTMX live search
3. Task 5.3: SSE progress
4. Task 5.4: Waveform preview

### Weeks 3-4: Complete Phase 6
1. Task 6.1: Svelte 5 setup
2. Task 6.2: Tauri IPC commands
3. Task 6.3: Svelte components
4. Task 6.4: Production builds

### Week 5: Complete Phase 7
1. Task 7.1: Filesystem export
2. Task 7.2: AppleScript automation

### Weeks 6-7: Complete Phase 8
1. Task 8.1: JUCE project setup
2. Task 8.2: Python sidecar server

### Week 8: Complete Phase 9
1. Task 9.1: Pack format implementation

### Weeks 9-10: Complete Phase 10
1. Task 10.1: macOS signing and notarization

---

## Critical Path Dependencies

```
Phase 4 (CLI) ──┬──> Phase 5 (Web UI) ──> Phase 6 (Desktop) ──> Phase 10 (Release)
                │
                └──> Phase 9 (Packs) ──────────────────────────┘
                
Phase 6 (Desktop) ──> Phase 7 (FL Studio) ──> Phase 8 (Plugin) ──> Phase 10 (Release)
```

**Parallel tracks:**
- Track A: Phase 4 → 5 → 6 → 10 (Core app)
- Track B: Phase 6 → 7 → 8 → 10 (DAW integration)
- Track C: Phase 4 → 9 → 10 (Pack system)

---

## Success Criteria for Each Phase

### Phase 4 Complete When:
- [ ] `samplemind import --workers 4` completes 100 files in <30s
- [ ] FTS5 search returns results in <50ms
- [ ] Single file analysis <500ms
- [ ] All 81 tests pass

### Phase 5 Complete When:
- [ ] HTMX search works without page reload
- [ ] SSE shows real-time import progress
- [ ] Waveform preview renders in <500ms
- [ ] Dark theme toggle works

### Phase 6 Complete When:
- [ ] Svelte 5 UI replaces Flask WebView
- [ ] macOS .dmg builds successfully
- [ ] Windows .msi builds successfully
- [ ] App starts in <2s

### Phase 7 Complete When:
- [ ] Samples export to FL Studio folder
- [ ] AppleScript automation works on macOS
- [ ] Metadata preserved in export

### Phase 8 Complete When:
- [ ] VST3 plugin loads in FL Studio
- [ ] AU plugin loads in Logic Pro
- [ ] Search works from plugin UI
- [ ] Sidecar starts automatically

### Phase 9 Complete When:
- [ ] .smpack export/import works
- [ ] SHA-256 verification passes
- [ ] Pack metadata preserved

### Phase 10 Complete When:
- [ ] macOS app is signed and notarized
- [ ] Windows app is signed
- [ ] GitHub Actions builds all platforms
- [ ] Auto-updater works

---

## Agent Assignment

| Phase | Primary Agent | Support Agents |
|-------|--------------|----------------|
| Phase 4 | `phase-04-cli` | `audio-analyzer`, `test-runner` |
| Phase 5 | `phase-05-web` | `doc-writer` |
| Phase 6 | `phase-06-desktop`, `tauri-builder` | `test-runner` |
| Phase 7 | `phase-07-fl-studio`, `fl-studio-agent` | `doc-writer` |
| Phase 8 | `phase-08-vst-plugin`, `fl-studio-agent` | `tauri-builder` |
| Phase 9 | `phase-09-sample-packs` | `test-runner` |
| Phase 10 | `phase-10-production`, `tauri-builder` | All agents |

---

## Daily Execution Template

```markdown
## Day N: [Phase X.Y Task Name]

**Agent:** `phase-XX-name`
**Files:** `path/to/file.py`
**Estimated time:** X hours

### Pre-flight checklist:
- [ ] All tests passing
- [ ] No uncommitted changes
- [ ] Branch created: `phase-X/task-Y`

### Implementation steps:
1. Step 1
2. Step 2
3. Step 3

### Acceptance criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass

### Commit message:
```
feat(phase-X): implement task Y

- Detail 1
- Detail 2

Closes #issue-number
```
```

---

**END OF EXECUTION PLAN**

*This document should be updated after each phase completion.*
