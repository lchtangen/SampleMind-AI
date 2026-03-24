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
from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository
from pathlib import Path

library_bp = Blueprint("library", __name__)


@library_bp.before_app_request
def setup():
    init_db()


@library_bp.route("/")
def index():
    """Main page — returns full HTML on normal request."""
    repo = SampleRepository()
    samples = repo.search()
    return render_template("index.html", samples=samples, total=repo.count())


@library_bp.route("/samples/partial")
def samples_partial():
    """
    HTMX partial: returns only the table, not the whole page.
    Called when search filters change.
    """
    repo = SampleRepository()
    samples = repo.search(
        query=request.args.get("q"),
        energy=request.args.get("energy"),
        instrument=request.args.get("instrument"),
        bpm_min=float(request.args["bpm_min"]) if request.args.get("bpm_min") else None,
        bpm_max=float(request.args["bpm_max"]) if request.args.get("bpm_max") else None,
        key=request.args.get("key"),
        genre=request.args.get("genre"),
    )
    return render_template("partials/sample_table.html", samples=samples)


@library_bp.route("/audio/<int:sample_id>")
def audio(sample_id: int):
    """Serve the audio file for a sample (for waveform preview)."""
    from sqlmodel import Session
    from samplemind.models import Sample
    from samplemind.data.db import engine

    with Session(engine) as session:
        sample = session.get(Sample, sample_id)
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
from flask import Blueprint, request, Response, stream_with_context
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository
from samplemind.models import SampleCreate

import_bp = Blueprint("import_", __name__)


def _sse_event(event_type: str, data: dict) -> str:
    """
    Format an SSE message.
    Format: "event: TYPE\ndata: JSON\n\n"
    Double newline ends one message.
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@import_bp.route("/api/import", methods=["POST"])
def import_folder():
    """
    Import endpoint with SSE streaming.
    Sends progress updates along the way and a done message at the end.
    """
    folder = Path(request.json.get("folder", ""))
    if not folder.is_dir():
        return {"error": "Folder not found"}, 400

    wav_files = list(folder.glob("**/*.wav"))

    def generate():
        """Generator that streams SSE events."""
        init_db()
        repo = SampleRepository()
        total = len(wav_files)

        # Send start event
        yield _sse_event("start", {"total": total})

        imported = 0
        for i, wav in enumerate(wav_files, 1):
            try:
                analysis = analyze_file(str(wav))
                data = SampleCreate(filename=wav.name, path=str(wav.resolve()), **analysis)
                sample = repo.upsert(data)
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

        # Send done event
        yield _sse_event("done", {"imported": imported, "total": total})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Important: disable Nginx buffering
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
from samplemind.data.db import init_db


@pytest.fixture
def client(tmp_path):
    """Flask test client with in-memory database."""
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        with app.app_context():
            init_db()
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
