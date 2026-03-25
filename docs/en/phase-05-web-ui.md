# Phase 5 — Web UI with Flask and HTMX

> Upgrade the Flask application to a `create_app()` factory with Blueprints, and replace
> manual JavaScript with **HTMX** for live updates and SSE for import progress.

---

## Prerequisites

- Phases 1–4 complete
- Flask 3.x in `pyproject.toml`
- Basic HTML/CSS/JavaScript knowledge

---

## Goal State

- `create_app()` factory pattern (Flask best practice)
- Blueprint structure for library and import
- Live search with HTMX (replaces JS `debounce`)
- Import progress as SSE stream (Server-Sent Events)
- Waveform preview with Wavesurfer.js
- Jinja2 macros for reusable UI components

---

## 1. Flask 3.x — Application Factory Pattern

The current `app = Flask(__name__)` at module level in `web/app.py` makes testing difficult.
Application Factory solves this:

```python
# OLD — hard to test and configure
app = Flask(__name__)

@app.route("/")
def index(): ...

# NEW — factory pattern
def create_app(config=None):
    app = Flask(__name__)
    if config:
        app.config.update(config)
    from .blueprints.library import library_bp
    app.register_blueprint(library_bp)
    return app
```

With the factory pattern you can create the app with test data in tests:
```python
# In test:
app = create_app({"TESTING": True, "DATABASE": ":memory:"})
client = app.test_client()
```

---

## 2. Blueprint Structure

```python
# filename: src/samplemind/web/app.py

from flask import Flask


def create_app(config: dict = None) -> Flask:
    """
    Application factory — creates and configures the Flask app.
    Call this from the serve command and in tests.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config.setdefault("SECRET_KEY", "samplemind-dev-key")
    app.config.setdefault("MAX_CONTENT_LENGTH", 500 * 1024 * 1024)  # 500 MB max upload

    if config:
        app.config.update(config)

    from samplemind.web.blueprints.library import library_bp
    from samplemind.web.blueprints.import_ import import_bp

    app.register_blueprint(library_bp)
    app.register_blueprint(import_bp)

    return app
```

```python
# filename: src/samplemind/web/blueprints/library.py

from flask import Blueprint, render_template, request, send_file, abort
from pathlib import Path

from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

library_bp = Blueprint("library", __name__)


@library_bp.before_app_request
def setup() -> None:
    """Ensure all SQLModel tables exist before the first request.

    init_orm() is idempotent — safe to call on every startup.
    It imports both models and calls SQLModel.metadata.create_all(engine).
    """
    init_orm()


@library_bp.route("/")
def index():
    """Main page — returns full HTML on normal request."""
    samples = SampleRepository.search()   # no filters → all samples
    return render_template("index.html", samples=samples, total=SampleRepository.count())


@library_bp.route("/samples/partial")
def samples_partial():
    """
    HTMX partial: returns only the table, not the whole page.
    Called when any search filter changes (triggered by hx-get on the inputs).
    All filter parameters are optional — omitting one means "any value".
    """
    samples = SampleRepository.search(
        query=request.args.get("q"),          # full-text search on filename/tags
        energy=request.args.get("energy"),    # "low" | "mid" | "high"
        instrument=request.args.get("instrument"),
        bpm_min=float(request.args["bpm_min"]) if request.args.get("bpm_min") else None,
        bpm_max=float(request.args["bpm_max"]) if request.args.get("bpm_max") else None,
        key=request.args.get("key"),
        genre=request.args.get("genre"),
    )
    return render_template("partials/sample_table.html", samples=samples)


@library_bp.route("/audio/<int:sample_id>")
def audio(sample_id: int):
    """Serve the audio file for a sample (for waveform preview).

    SampleRepository.get_by_id() looks up the integer row id (not the UUID user_id).
    Returns 404 if the row doesn't exist or the file has been moved/deleted.
    """
    sample = SampleRepository.get_by_id(sample_id)
    if not sample:
        abort(404)
    path = Path(sample.path)
    if not path.exists():
        abort(404)
    return send_file(str(path), mimetype="audio/wav")
```

---

## 3. HTMX — Live Search Without JavaScript

HTMX lets you build dynamic UIs with HTML attributes instead of JavaScript.

### Core HTMX Attributes

```
hx-get="/url"         → Make a GET request to /url
hx-post="/url"        → Make a POST request
hx-trigger="input"    → Fire the request on input event
hx-target="#id"       → Insert response into element with id="id"
hx-swap="innerHTML"   → Replace content (default)
```

### Live Search with Debounce

```html
<!-- filename: src/samplemind/web/templates/partials/filter_bar.html -->

<!-- hx-trigger="input delay:300ms" waits 300ms after the last keystroke
     before sending the request — replaces the JS debounce function -->
<div class="filter-bar">
  <input
    type="text"
    name="q"
    placeholder="Search samples..."
    hx-get="/samples/partial"
    hx-trigger="input delay:300ms, keyup[key=='Enter']"
    hx-target="#sample-table-container"
    hx-swap="innerHTML"
    hx-include="[name='energy'],[name='instrument'],[name='bpm_min'],[name='bpm_max']"
  >

  <!-- Dropdown filters — also trigger live updates -->
  <select
    name="energy"
    hx-get="/samples/partial"
    hx-trigger="change"
    hx-target="#sample-table-container"
    hx-swap="innerHTML"
    hx-include="[name='q'],[name='instrument'],[name='bpm_min'],[name='bpm_max']"
  >
    <option value="">All energy levels</option>
    <option value="low">Low energy</option>
    <option value="mid">Mid energy</option>
    <option value="high">High energy</option>
  </select>

  <select name="instrument" hx-get="/samples/partial" hx-trigger="change"
          hx-target="#sample-table-container" hx-swap="innerHTML"
          hx-include="[name='q'],[name='energy'],[name='bpm_min'],[name='bpm_max']">
    <option value="">All types</option>
    <option value="kick">Kick</option>
    <option value="snare">Snare</option>
    <option value="hihat">Hi-hat</option>
    <option value="bass">Bass</option>
    <option value="pad">Pad</option>
    <option value="lead">Lead</option>
    <option value="loop">Loop</option>
  </select>
</div>

<!-- Table container — HTMX inserts its responses here -->
<div id="sample-table-container">
  {% include "partials/sample_table.html" %}
</div>
```

```html
<!-- filename: src/samplemind/web/templates/partials/sample_table.html -->
<!-- This is the HTMX fragment returned by /samples/partial -->

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
    {% for sample in samples %}
    <tr class="sample-row" data-id="{{ sample.id }}">
      <td>{{ sample.filename }}</td>
      <td>{{ sample.bpm or "?" }}</td>
      <td>{{ sample.key or "" }}</td>
      <td>{{ sample.instrument or "" }}</td>
      <td>{{ sample.energy or "" }}</td>
      <td>{{ sample.mood or "" }}</td>
      <td>
        <!-- Wavesurfer button — initialised by app.js on click -->
        <button class="play-btn" data-sample-id="{{ sample.id }}">▶</button>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="7">No samples found.</td></tr>
    {% endfor %}
  </tbody>
</table>
```

---

## 4. SSE — Import Progress in Real-Time

Server-Sent Events let the server push updates to the browser without polling.

```python
# filename: src/samplemind/web/blueprints/import_.py

import json
from pathlib import Path

from flask import Blueprint, Response, request, stream_with_context

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

import_bp = Blueprint("import_", __name__)


def _sse_event(event_type: str, data: dict) -> str:
    """
    Format one Server-Sent Events message.

    SSE wire format:
      event: <TYPE>\\n
      data: <JSON>\\n
      \\n       ← blank line terminates the message

    The browser's EventSource API parses this automatically.
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@import_bp.route("/api/import", methods=["POST"])
def import_folder():
    """
    Import endpoint with SSE streaming.

    The client POSTs {"folder": "/abs/path/to/samples"} and keeps the
    connection open. The server streams one SSE event per file until done.
    This avoids blocking the browser for large libraries.
    """
    folder = Path(request.json.get("folder", ""))
    if not folder.is_dir():
        return {"error": "Folder not found"}, 400

    wav_files = list(folder.glob("**/*.wav"))

    def generate():
        """Generator that yields SSE events — one per WAV file analysed."""
        # Ensure the database tables exist before the first upsert.
        # init_orm() is idempotent — safe to call multiple times.
        init_orm()
        total = len(wav_files)

        # Notify the client of the total file count upfront
        yield _sse_event("start", {"total": total})

        imported = 0
        for i, wav in enumerate(wav_files, 1):
            try:
                analysis = analyze_file(str(wav))
                sample_data = SampleCreate(
                    filename=wav.name,
                    path=str(wav.resolve()),
                    **analysis,        # bpm, key, mood, energy, instrument
                )
                # SampleRepository.upsert() is a static method — no instance needed.
                # It inserts on first import and updates auto-detected fields on re-import.
                # Manually tagged fields (genre, tags) are never overwritten.
                SampleRepository.upsert(sample_data)
                imported += 1

                # Send progress for each file
                yield _sse_event("progress", {
                    "current": i,
                    "total": total,
                    "filename": wav.name,
                    "analysis": analysis,
                })
            except Exception as e:
                yield _sse_event("error", {"filename": wav.name, "error": str(e)})

        # Final event — client closes the EventSource on receipt
        yield _sse_event("done", {"imported": imported, "total": total})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Critical: disable Nginx/proxy response buffering
        },
    )
```

Frontend code to consume SSE:

```javascript
// filename: src/samplemind/web/static/app.js (import section)

function startImport(folderPath) {
  const progressBar = document.getElementById("import-progress");
  const statusText = document.getElementById("import-status");

  fetch("/api/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder: folderPath }),
  }).then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    function readChunk() {
      reader.read().then(({ done, value }) => {
        if (done) return;

        const text = decoder.decode(value);
        const lines = text.split("\n");
        let eventType = "";
        let eventData = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) eventType = line.slice(7);
          if (line.startsWith("data: ")) eventData = line.slice(6);
          if (line === "" && eventType && eventData) {
            const data = JSON.parse(eventData);
            handleEvent(eventType, data);
            eventType = ""; eventData = "";
          }
        }
        readChunk();
      });
    }
    readChunk();
  });
}

function handleEvent(type, data) {
  const progressBar = document.getElementById("import-progress");
  const statusText = document.getElementById("import-status");

  if (type === "start") {
    statusText.textContent = `Starting import of ${data.total} files...`;
  } else if (type === "progress") {
    const pct = Math.round((data.current / data.total) * 100);
    progressBar.style.width = `${pct}%`;
    statusText.textContent = `${data.current}/${data.total}: ${data.filename}`;
  } else if (type === "done") {
    statusText.textContent = `Done! Imported ${data.imported} of ${data.total} samples.`;
    htmx.trigger("#sample-table-container", "refresh");
  }
}
```

---

## 5. Waveform Preview with Wavesurfer.js

```html
<!-- filename: src/samplemind/web/templates/index.html (head section) -->

<!-- Wavesurfer.js via CDN — no bundler needed -->
<script src="https://unpkg.com/wavesurfer.js@7"></script>
```

```javascript
// filename: src/samplemind/web/static/app.js (waveform section)

let activeWaveSurfer = null;

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".play-btn");
  if (!btn) return;

  const sampleId = btn.dataset.sampleId;
  const row = btn.closest("tr");

  // Stop previous playback
  if (activeWaveSurfer) {
    activeWaveSurfer.destroy();
    activeWaveSurfer = null;
  }

  // Create waveform container in the row
  let waveContainer = row.querySelector(".waveform-inline");
  if (!waveContainer) {
    waveContainer = document.createElement("div");
    waveContainer.className = "waveform-inline";
    waveContainer.style.cssText = "height:40px;width:200px;display:inline-block;";
    btn.parentNode.insertBefore(waveContainer, btn.nextSibling);
  }

  // Initialise Wavesurfer
  activeWaveSurfer = WaveSurfer.create({
    container: waveContainer,
    waveColor: "#6366f1",
    progressColor: "#4f46e5",
    height: 40,
    barWidth: 2,
    url: `/audio/${sampleId}`,
  });

  activeWaveSurfer.on("ready", () => {
    activeWaveSurfer.play();
    btn.textContent = "⏸";
  });

  activeWaveSurfer.on("finish", () => {
    btn.textContent = "▶";
  });
});
```

---

## 6. Jinja2 Macros

```html
<!-- filename: src/samplemind/web/templates/macros/ui.html -->

{# Macro for one sample row — reusable in all contexts #}
{% macro sample_row(sample) %}
<tr class="sample-row" data-id="{{ sample.id }}">
  <td class="filename">{{ sample.filename }}</td>
  <td class="bpm">{{ "%.1f"|format(sample.bpm) if sample.bpm else "—" }}</td>
  <td>{{ sample.key or "—" }}</td>
  <td><span class="badge badge-{{ sample.instrument }}">{{ sample.instrument or "—" }}</span></td>
  <td><span class="badge badge-{{ sample.energy }}">{{ sample.energy or "—" }}</span></td>
  <td>{{ sample.mood or "—" }}</td>
  <td><button class="play-btn" data-sample-id="{{ sample.id }}">▶</button></td>
</tr>
{% endmacro %}

{# Toast notification #}
{% macro toast(message, type="info") %}
<div class="toast toast-{{ type }}" role="alert">
  {{ message }}
</div>
{% endmacro %}
```

---

## 7. Tests with Flask Test Client

```python
# filename: tests/test_web.py

import pytest
from samplemind.web.app import create_app
from samplemind.data.orm import init_orm


@pytest.fixture
def client(tmp_path):
    """Flask test client with in-memory database.

    Uses the application factory (create_app) so each test gets a fresh
    Flask app.  init_orm() creates all SQLModel tables in the ORM engine
    (which in tests should be redirected to a StaticPool in-memory SQLite
    via the orm_engine fixture, then call init_orm() to create tables).
    """
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        with app.app_context():
            init_orm()   # creates users + samples tables if they don't exist
        yield c


def test_index_returns_200(client):
    """Main page should return HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_samples_partial_returns_html(client):
    """HTMX partial should return HTML fragment (not full page)."""
    response = client.get("/samples/partial")
    assert response.status_code == 200
    assert b"<table>" in response.data or b"No samples" in response.data


def test_audio_404_for_unknown_id(client):
    """Audio endpoint for unknown ID should return 404."""
    response = client.get("/audio/99999")
    assert response.status_code == 404
```

---

## Migration Notes

- `src/web/app.py` is replaced by `create_app()` factory and Blueprint files
- `src/web/templates/index.html` is updated with HTMX attributes and includes partials
- `src/web/static/app.js` keeps waveform and Tauri-specific code; JS debounce is removed

---

## Testing Checklist

```bash
# Start the web UI
$ uv run samplemind serve

# Open in browser: http://localhost:5000

# Confirm live search works (type in search field)
# Confirm energy filter works (select from dropdown)
# Confirm audio playback works

# Run automated tests
$ uv run pytest tests/test_web.py -v
```

---

## Troubleshooting

**HTMX requests not working**
```html
<!-- Check that the HTMX script is loaded in <head> -->
<script src="https://unpkg.com/htmx.org@2"></script>
```

**SSE stops after 30 seconds**
```python
# Flask has a default timeout. For long imports, increase it:
app.config["PERMANENT_SESSION_LIFETIME"] = 3600
```

**Waveform not loading**
```
Check that the /audio/<id> route returns the correct MIME type (audio/wav)
and that the file path in the database still exists.
```

---

## 8. Web UI Enhancements (2026)

### Flask-CORS

Add `flask-cors` to support Tauri WebView cross-origin requests:

```bash
uv add flask-cors
```

```python
# src/samplemind/web/app.py
from flask import Flask
from flask_cors import CORS

from samplemind.core.config import get_settings


def create_app(config: dict | None = None) -> Flask:
    """Application factory — creates and configures the Flask app.

    Call this from the serve command and in tests.
    CORS is configured to allow Tauri WebView and local dev origins from Settings.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    settings = get_settings()
    app.secret_key = settings.FLASK_SECRET_KEY
    app.config.setdefault("MAX_CONTENT_LENGTH", 500 * 1024 * 1024)  # 500 MB max upload

    if config:
        app.config.update(config)

    # Allow all origins listed in Settings.CORS_ORIGINS:
    #   "http://localhost:5174"  — Tauri dev
    #   "http://localhost:5000"  — Flask dev
    #   "http://localhost:8000"  — FastAPI dev
    #   "tauri://localhost"      — Tauri production
    CORS(app, origins=settings.CORS_ORIGINS)

    # Register blueprints once the CORS middleware is installed
    from samplemind.web.blueprints.library import library_bp
    from samplemind.web.blueprints.import_ import import_bp

    app.register_blueprint(library_bp)
    app.register_blueprint(import_bp)

    return app
```

### Dark Mode

Add CSS custom properties and `prefers-color-scheme` support:

```css
/* src/samplemind/web/static/css/app.css */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --accent: #0d6efd;
  --border: #dee2e6;
}

[data-theme="dark"] {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --accent: #e94560;
  --border: #2d3748;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    /* ... */
  }
}
```

Toggle button in template:
```html
<!-- templates/base.html -->
<button id="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">
  🌙
</button>
<script>
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  document.documentElement.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
  localStorage.setItem('theme', document.documentElement.getAttribute('data-theme'));
}
// Restore saved preference:
const saved = localStorage.getItem('theme');
if (saved) document.documentElement.setAttribute('data-theme', saved);
</script>
```

### Keyboard Shortcuts

Add global keyboard shortcuts for power users:

```javascript
// src/samplemind/web/static/js/shortcuts.js
document.addEventListener('keydown', (e) => {
  // Don't trigger when typing in an input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

  switch (e.key) {
    case 'j':  // Navigate down
      selectNextSample();
      break;
    case 'k':  // Navigate up
      selectPrevSample();
      break;
    case ' ':  // Play/pause selected sample
      e.preventDefault();
      togglePlayback();
      break;
    case 't':  // Open tag editor
      openTagEditor(getSelectedSampleId());
      break;
    case 'e':  // Export to FL Studio
      exportToFLStudio(getSelectedSampleId());
      break;
    case '/':  // Focus search box
      e.preventDefault();
      document.getElementById('search-input').focus();
      break;
    case 'Escape':  // Clear selection / close modal
      clearSelection();
      break;
  }
});
```

### Bulk Tag Endpoint

```python
# src/samplemind/web/blueprints/library.py
from flask import request, jsonify

@bp.post("/api/samples/bulk-tag")
def bulk_tag():
    """Bulk add/remove/replace tags on multiple samples.

    Body: {"ids": [1, 2, 3], "tags": ["dark", "trap"], "mode": "add"|"remove"|"replace"}
    """
    data = request.get_json()
    ids: list[int] = data.get("ids", [])
    tags: list[str] = data.get("tags", [])
    mode: str = data.get("mode", "add")  # add | remove | replace

    if not ids or not tags:
        return jsonify({"error": "ids and tags are required"}), 400
    if mode not in ("add", "remove", "replace"):
        return jsonify({"error": "mode must be add, remove, or replace"}), 400

    updated = bulk_update_tags(ids, tags, mode)
    return jsonify({"updated": updated, "ids": ids})
```

Example HTMX call from the UI:
```html
<button hx-post="/api/samples/bulk-tag"
        hx-vals='{"ids": [1,2,3], "tags": ["dark"], "mode": "add"}'
        hx-target="#tag-status"
        hx-swap="innerHTML">
  Add "dark" tag to selected
</button>
```

### SSE Progress Stream for Bulk Operations

```python
# src/samplemind/web/blueprints/import_bp.py
import json
from flask import Response, stream_with_context

@bp.get("/api/import/progress")
def import_progress():
    """Server-Sent Events stream for import progress.

    Client connects once; server pushes progress events until complete.
    """
    def generate():
        for i, result in enumerate(run_import_with_progress()):
            data = json.dumps({"completed": i + 1, "total": result["total"],
                               "file": result["file"], "status": result["status"]})
            yield f"data: {data}\n\n"
        yield "data: {\"done\": true}\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

Client-side (HTMX + JS):
```javascript
const source = new EventSource('/api/import/progress');
source.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.done) { source.close(); return; }
  updateProgressBar(data.completed, data.total);
};

---

## 8. WebSocket Real-Time Updates

While SSE works for import progress, **WebSocket** enables full bidirectional
communication — the server can push updates when any client changes data.

```bash
uv add flask-socketio eventlet
```

```python
# src/samplemind/web/socketio_ext.py
"""
Flask-SocketIO extension for real-time library updates.

Events emitted by server → client:
  sample_imported   → new sample added {id, filename, instrument, mood}
  sample_tagged     → metadata updated {id, field, value}
  import_progress   → {current, total, filename}
  import_complete   → {imported, duplicates, errors}

Events received from client → server:
  subscribe_library → start streaming updates to this client
  search            → {query} → server emits search_results
"""
from flask_socketio import SocketIO, emit, join_room

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def push_sample_imported(sample_dict: dict) -> None:
    """Push to all connected clients when a sample is imported."""
    socketio.emit("sample_imported", sample_dict, room="library")


def push_import_progress(current: int, total: int, filename: str) -> None:
    socketio.emit("import_progress",
                  {"current": current, "total": total, "filename": filename},
                  room="library")


@socketio.on("subscribe_library")
def on_subscribe():
    """Client asks to join the library room for live updates."""
    join_room("library")
    emit("subscribed", {"room": "library"})


@socketio.on("search")
def on_search(data: dict):
    """Client sends a search query; server responds with results."""
    from samplemind.data.fts import fts_search
    query = data.get("query", "")
    results = fts_search(query, limit=50) if query else []
    emit("search_results", {"query": query, "results": results})
```

Frontend JavaScript (add to `static/app.js`):

```javascript
// Real-time library updates via Socket.IO
const socket = io();

socket.on('connect', () => {
  socket.emit('subscribe_library');
});

socket.on('sample_imported', (sample) => {
  // Prepend new sample card to the library grid
  const card = buildSampleCard(sample);
  document.querySelector('#sample-grid').prepend(card);
  showToast(`Imported: ${sample.filename}`);
});

socket.on('import_progress', ({current, total, filename}) => {
  const pct = Math.round((current / total) * 100);
  document.querySelector('#progress-bar').style.width = pct + '%';
  document.querySelector('#progress-label').textContent = `${current}/${total} — ${filename}`;
});

socket.on('import_complete', ({imported, duplicates, errors}) => {
  showToast(`Done: ${imported} imported, ${duplicates} duplicates, ${errors} errors`, 'success');
  document.querySelector('#progress-bar').style.width = '0%';
});

// Live search via WebSocket
document.querySelector('#search-input').addEventListener('input', (e) => {
  socket.emit('search', { query: e.target.value });
});

socket.on('search_results', ({results}) => {
  renderSamples(results);
});
```

---

## 9. Playlist Builder

Drag samples into a playlist, reorder, and export as M3U, JSON, or FL Studio `.fst`.

```python
# src/samplemind/web/routes/playlist.py
"""
Playlist CRUD routes.

Playlists are stored in the `playlists` and `playlist_items` tables.
Each playlist has an ordered list of sample IDs.

Routes:
  GET  /playlists              → list all playlists
  POST /playlists              → create {name, description}
  GET  /playlists/<id>         → get playlist with samples
  POST /playlists/<id>/add     → add sample {sample_id, position}
  POST /playlists/<id>/reorder → {items: [{id, position}]}
  DELETE /playlists/<id>       → delete playlist
  GET  /playlists/<id>/export  → ?format=m3u|json|fst
"""
from flask import Blueprint, request, jsonify, Response
from samplemind.data.repositories.playlist_repository import PlaylistRepository

bp = Blueprint("playlists", __name__, url_prefix="/playlists")


@bp.route("", methods=["GET"])
def list_playlists():
    return jsonify(PlaylistRepository.get_all())


@bp.route("", methods=["POST"])
def create_playlist():
    data = request.get_json()
    playlist = PlaylistRepository.create(
        name=data["name"],
        description=data.get("description", ""),
    )
    return jsonify(playlist), 201


@bp.route("/<int:playlist_id>/export")
def export_playlist(playlist_id: int):
    fmt = request.args.get("format", "json")
    playlist = PlaylistRepository.get_with_samples(playlist_id)
    if not playlist:
        return jsonify({"error": "not found"}), 404

    if fmt == "m3u":
        lines = ["#EXTM3U", f"#PLAYLIST:{playlist['name']}"]
        for item in playlist["items"]:
            lines.append(f"#EXTINF:-1,{item['filename']}")
            lines.append(item["path"])
        return Response("\n".join(lines), mimetype="audio/x-mpegurl",
                        headers={"Content-Disposition": f"attachment; filename={playlist['name']}.m3u"})

    return jsonify(playlist)
```

HTMX drag-and-drop for reordering (using Sortable.js):

```html
<!-- templates/playlist.html -->
<ul id="playlist-items"
    hx-post="/playlists/{{ playlist.id }}/reorder"
    hx-trigger="end"
    hx-swap="none">
  {% for item in playlist.items %}
  <li class="draggable" data-id="{{ item.id }}">
    <span class="drag-handle">⠿</span>
    <span class="filename">{{ item.filename }}</span>
    <span class="meta">{{ item.instrument }} · {{ item.bpm }} BPM</span>
    <button hx-delete="/playlists/{{ playlist.id }}/items/{{ item.id }}"
            hx-target="closest li" hx-swap="outerHTML">✕</button>
  </li>
  {% endfor %}
</ul>
<script>
  Sortable.create(document.getElementById('playlist-items'), {
    handle: '.drag-handle',
    animation: 150,
    onEnd() {
      const items = [...document.querySelectorAll('#playlist-items li')]
        .map((el, i) => ({ id: el.dataset.id, position: i }));
      htmx.trigger('#playlist-items', 'end', { items });
    }
  });
</script>
```

---

## 10. Waveform Visualizer

Render sample waveforms in the browser using **WaveSurfer.js** — no server-side
processing needed; WaveSurfer streams audio directly from `/audio/<id>`.

```html
<!-- templates/sample_card.html -->
<div id="waveform-{{ sample.id }}" class="waveform-container"></div>
<div class="waveform-controls">
  <button onclick="ws_{{ sample.id }}.playPause()">▶/⏸</button>
  <button onclick="ws_{{ sample.id }}.stop()">⏹</button>
  <span class="time" id="time-{{ sample.id }}">0:00</span>
</div>

<script type="module">
import WaveSurfer from 'https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.esm.js';

const ws_{{ sample.id }} = WaveSurfer.create({
  container: '#waveform-{{ sample.id }}',
  url: '/audio/{{ sample.id }}',
  waveColor: '#6366f1',       // indigo
  progressColor: '#a5b4fc',   // lighter indigo
  height: 48,
  barWidth: 2,
  barGap: 1,
  interact: true,
  normalize: true,
});

ws_{{ sample.id }}.on('timeupdate', (t) => {
  const m = Math.floor(t / 60);
  const s = String(Math.floor(t % 60)).padStart(2, '0');
  document.getElementById('time-{{ sample.id }}').textContent = `${m}:${s}`;
});
</script>
```

Flask audio streaming with HTTP range request support (for seeking):

```python
@app.route("/audio/<int:sample_id>")
@login_required
def stream_audio(sample_id: int):
    """
    Stream WAV file with HTTP Range support.
    WaveSurfer requires Range requests for large files.
    Flask's send_file with conditional=True enables this automatically.
    """
    from samplemind.data.repositories.sample_repository import SampleRepository
    sample = SampleRepository.get_by_id(sample_id)
    if not sample or not Path(sample.path).exists():
        abort(404)
    return send_file(sample.path, mimetype="audio/wav", conditional=True,
                     etag=True, last_modified=Path(sample.path).stat().st_mtime)
```
```

