# Fase 5 — Web UI med Flask og HTMX

> Oppgrader Flask-applikasjonen til en `create_app()`-factory med Blueprints, og erstatt
> manuell JavaScript med **HTMX** for live-oppdatering og SSE for import-fremgang.

---

## Forutsetninger

- Fase 1–4 fullført
- Flask 3.x i `pyproject.toml`
- Grunnleggende HTML/CSS/JavaScript-kunnskap

---

## Mål etter denne fasen

- `create_app()` factory-mønster (Flask best practice)
- Blueprint-struktur for library og import
- Live-søk med HTMX (erstatter JS `debounce`)
- Import-fremgang som SSE-stream (Server-Sent Events)
- Waveform-preview med Wavesurfer.js
- Jinja2 makroer for gjenbrukbare UI-komponenter

---

## 1. Flask 3.x — Application Factory-mønsteret

Det nåværende `app = Flask(__name__)` på modulnivå i `web/app.py` gjør testing vanskelig.
Application Factory løser dette:

```python
# GAMMELT — vanskelig å teste og konfigurere
app = Flask(__name__)

@app.route("/")
def index(): ...

# NYTT — factory-mønster
def create_app(config=None):
    app = Flask(__name__)
    # Konfigurer etter behov
    if config:
        app.config.update(config)
    # Registrer blueprints
    from .blueprints.library import library_bp
    app.register_blueprint(library_bp)
    return app
```

Med factory-mønsteret kan du opprette appen med testdata i tester:
```python
# I test:
app = create_app({"TESTING": True, "DATABASE": ":memory:"})
client = app.test_client()
```

---

## 2. Blueprint-struktur

```python
# filename: src/samplemind/web/app.py

from flask import Flask


def create_app(config: dict = None) -> Flask:
    """
    Application factory — oppretter og konfigurerer Flask-appen.
    Kall denne fra serve-kommandoen og i tester.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Standard konfigurasjon
    app.config.setdefault("SECRET_KEY", "samplemind-dev-key")
    app.config.setdefault("MAX_CONTENT_LENGTH", 500 * 1024 * 1024)  # 500 MB maks upload

    if config:
        app.config.update(config)

    # Registrer blueprints
    from samplemind.web.blueprints.library import library_bp
    from samplemind.web.blueprints.import_ import import_bp

    app.register_blueprint(library_bp)
    app.register_blueprint(import_bp)

    return app
```

```python
# filename: src/samplemind/web/blueprints/library.py

from pathlib import Path

from flask import Blueprint, abort, render_template, request, send_file

from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

library_bp = Blueprint("library", __name__)


@library_bp.before_app_request
def setup() -> None:
    """Sikrer at alle SQLModel-tabeller eksisterer før første forespørsel.

    init_orm() er idempotent — trygt å kalle ved hver oppstart.
    """
    init_orm()


@library_bp.route("/")
def index():
    """Hoved-side — returnerer full HTML ved normal forespørsel."""
    # SampleRepository bruker statiske metoder — ingen instans nødvendig
    samples = SampleRepository.search()
    return render_template("index.html", samples=samples, total=SampleRepository.count())


@library_bp.route("/samples/partial")
def samples_partial():
    """
    HTMX-partial: returnerer kun tabellen, ikke hele siden.
    Kalles når søkefiltre endres (utløst av hx-get på input-feltene).
    """
    samples = SampleRepository.search(
        query=request.args.get("q"),
        energy=request.args.get("energy"),
        instrument=request.args.get("instrument"),
        bpm_min=float(request.args["bpm_min"]) if request.args.get("bpm_min") else None,
        bpm_max=float(request.args["bpm_max"]) if request.args.get("bpm_max") else None,
        key=request.args.get("key"),
        genre=request.args.get("genre"),
    )
    # Returner kun HTML-fragmentet (ikke full side)
    return render_template("partials/sample_table.html", samples=samples)


@library_bp.route("/audio/<int:sample_id>")
def audio(sample_id: int):
    """Serve audio-filen for en sample (for waveform-preview).

    SampleRepository.get_by_id() slår opp på heltalls-rad-id (ikke UUID user_id).
    Returnerer 404 hvis raden mangler eller filen er slettet/flyttet.
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

## 3. HTMX — Live-søk uten JavaScript

HTMX lar deg lage dynamiske UI-er med HTML-attributter i stedet for JavaScript.

### Grunnleggende HTMX-attributter

```
hx-get="/url"         → Gjør en GET-forespørsel til /url
hx-post="/url"        → Gjør en POST-forespørsel
hx-trigger="input"    → Utfør forespørselen ved input-hendelse
hx-target="#id"       → Sett svaret inn i elementet med id="id"
hx-swap="innerHTML"   → Erstatt innholdet (standard)
```

### Live-søk med debounce

```html
<!-- filename: src/samplemind/web/templates/partials/filter_bar.html -->

<!-- hx-trigger="input delay:300ms" venter 300ms etter siste tastetrykk
     før den sender forespørselen — erstatter JS debounce-funksjonen -->
<div class="filter-bar">
  <input
    type="text"
    name="q"
    placeholder="Søk i samples..."
    hx-get="/samples/partial"
    hx-trigger="input delay:300ms, keyup[key=='Enter']"
    hx-target="#sample-table-container"
    hx-swap="innerHTML"
    hx-include="[name='energy'],[name='instrument'],[name='bpm_min'],[name='bpm_max']"
  >

  <!-- Dropdown-filtre — triggerer også live-oppdatering -->
  <select
    name="energy"
    hx-get="/samples/partial"
    hx-trigger="change"
    hx-target="#sample-table-container"
    hx-swap="innerHTML"
    hx-include="[name='q'],[name='instrument'],[name='bpm_min'],[name='bpm_max']"
  >
    <option value="">Alle energinivåer</option>
    <option value="low">Lav energi</option>
    <option value="mid">Middels energi</option>
    <option value="high">Høy energi</option>
  </select>

  <select name="instrument" hx-get="/samples/partial" hx-trigger="change"
          hx-target="#sample-table-container" hx-swap="innerHTML"
          hx-include="[name='q'],[name='energy'],[name='bpm_min'],[name='bpm_max']">
    <option value="">Alle typer</option>
    <option value="kick">Kick</option>
    <option value="snare">Snare</option>
    <option value="hihat">Hi-hat</option>
    <option value="bass">Bass</option>
    <option value="pad">Pad</option>
    <option value="lead">Lead</option>
    <option value="loop">Loop</option>
  </select>
</div>

<!-- Tabellens container — her setter HTMX inn sine svar -->
<div id="sample-table-container">
  {% include "partials/sample_table.html" %}
</div>
```

```html
<!-- filename: src/samplemind/web/templates/partials/sample_table.html -->
<!-- Dette er HTMX-fragmentet som returneres av /samples/partial -->

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
    {% for sample in samples %}
    <tr class="sample-row" data-id="{{ sample.id }}">
      <td>{{ sample.filename }}</td>
      <td>{{ sample.bpm or "?" }}</td>
      <td>{{ sample.key or "" }}</td>
      <td>{{ sample.instrument or "" }}</td>
      <td>{{ sample.energy or "" }}</td>
      <td>{{ sample.mood or "" }}</td>
      <td>
        <!-- Wavesurfer-knapp — initialiseres av app.js ved klikk -->
        <button class="play-btn" data-sample-id="{{ sample.id }}">▶</button>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="7">Ingen samples funnet.</td></tr>
    {% endfor %}
  </tbody>
</table>
```

---

## 4. SSE — Import-fremgang i real-time

Server-Sent Events lar serveren pushe oppdateringer til nettleseren uten polling.

```python
# filename: src/samplemind/web/blueprints/import_.py

import json
from pathlib import Path
from flask import Blueprint, request, Response, stream_with_context
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

import_bp = Blueprint("import_", __name__)


def _sse_event(event_type: str, data: dict) -> str:
    """
    Formater en SSE-melding.
    Format: "event: TYPE\ndata: JSON\n\n"
    Dobbel newline avslutter én melding.
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@import_bp.route("/api/import", methods=["POST"])
def import_folder():
    """
    Import-endepunkt med SSE-streaming.
    Sender progress-oppdateringer underveis og en ferdig-melding til slutt.
    """
    folder = Path(request.json.get("folder", ""))
    if not folder.is_dir():
        return {"error": "Mappe finnes ikke"}, 400

    wav_files = list(folder.glob("**/*.wav"))

    def generate():
        """Generator som streamer SSE-events — én per WAV-fil analysert."""
        # Sikrer at tabellene finnes før første upsert. init_orm() er idempotent.
        init_orm()
        total = len(wav_files)

        # Varsle klienten om total filantall på forhånd
        yield _sse_event("start", {"total": total})

        imported = 0
        for i, wav in enumerate(wav_files, 1):
            try:
                analysis = analyze_file(str(wav))
                data = SampleCreate(filename=wav.name, path=str(wav.resolve()), **analysis)
                # SampleRepository.upsert() er en statisk metode — ingen instans nødvendig
                SampleRepository.upsert(data)
                imported += 1

                # Send fremgang for hver fil
                yield _sse_event("progress", {
                    "current": i,
                    "total": total,
                    "filename": wav.name,
                    "analysis": analysis,
                })
            except Exception as e:
                yield _sse_event("error", {"filename": wav.name, "error": str(e)})

        # Send ferdig-event
        yield _sse_event("done", {"imported": imported, "total": total})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Viktig: deaktiver Nginx-buffering
        },
    )
```

Frontend-kode for å konsumere SSE:

```javascript
// filename: src/samplemind/web/static/app.js (import-seksjon)

function startImport(folderPath) {
  const progressBar = document.getElementById("import-progress");
  const statusText = document.getElementById("import-status");

  // Åpne SSE-forbindelsen
  fetch("/api/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder: folderPath }),
  }).then(response => {
    // EventSource kan ikke lese POST-svar, men vi kan lese streamen direkte
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    function readChunk() {
      reader.read().then(({ done, value }) => {
        if (done) return;

        const text = decoder.decode(value);
        // Parse SSE-linjer
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
        readChunk(); // Les neste chunk
      });
    }
    readChunk();
  });
}

function handleEvent(type, data) {
  const progressBar = document.getElementById("import-progress");
  const statusText = document.getElementById("import-status");

  if (type === "start") {
    statusText.textContent = `Starter import av ${data.total} filer...`;
  } else if (type === "progress") {
    const pct = Math.round((data.current / data.total) * 100);
    progressBar.style.width = `${pct}%`;
    statusText.textContent = `${data.current}/${data.total}: ${data.filename}`;
  } else if (type === "done") {
    statusText.textContent = `Ferdig! Importerte ${data.imported} av ${data.total} samples.`;
    // Oppdater tabellen via HTMX
    htmx.trigger("#sample-table-container", "refresh");
  }
}
```

---

## 5. Waveform-preview med Wavesurfer.js

```html
<!-- filename: src/samplemind/web/templates/index.html (head-seksjon) -->

<!-- Wavesurfer.js via CDN — ingen bundler nødvendig -->
<script src="https://unpkg.com/wavesurfer.js@7"></script>
```

```javascript
// filename: src/samplemind/web/static/app.js (waveform-seksjon)

let activeWaveSurfer = null;

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".play-btn");
  if (!btn) return;

  const sampleId = btn.dataset.sampleId;
  const row = btn.closest("tr");

  // Avslutt forrige avspilling
  if (activeWaveSurfer) {
    activeWaveSurfer.destroy();
    activeWaveSurfer = null;
  }

  // Opprett waveform-container i raden
  let waveContainer = row.querySelector(".waveform-inline");
  if (!waveContainer) {
    waveContainer = document.createElement("div");
    waveContainer.className = "waveform-inline";
    waveContainer.style.cssText = "height:40px;width:200px;display:inline-block;";
    btn.parentNode.insertBefore(waveContainer, btn.nextSibling);
  }

  // Initialiser Wavesurfer
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

## 6. Jinja2 Makroer

```html
<!-- filename: src/samplemind/web/templates/macros/ui.html -->

{# Makro for én sample-rad — gjenbrukbar i alle kontekster #}
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

{# Toast-varsel #}
{% macro toast(message, type="info") %}
<div class="toast toast-{{ type }}" role="alert">
  {{ message }}
</div>
{% endmacro %}
```

---

## 7. Tester med Flask test-klient

```python
# filename: tests/test_web.py

import pytest
from samplemind.web.app import create_app
from samplemind.data.orm import init_orm


@pytest.fixture
def client(tmp_path):
    """Flask test-klient med in-memory database.

    init_orm() oppretter alle SQLModel-tabeller i ORM-motoren.
    I tester bør orm_engine-fixturet brukes for å omdirigere til in-memory SQLite.
    """
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        with app.app_context():
            init_orm()   # oppretter users + samples tabeller hvis de ikke finnes
        yield c


def test_index_returns_200(client):
    """Hoved-siden skal returnere HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_samples_partial_returns_html(client):
    """HTMX-partial skal returnere HTML-fragment (ikke full side)."""
    response = client.get("/samples/partial")
    assert response.status_code == 200
    assert b"<table>" in response.data or b"Ingen samples" in response.data


def test_audio_404_for_unknown_id(client):
    """Audio-endepunkt for ukjent ID skal returnere 404."""
    response = client.get("/audio/99999")
    assert response.status_code == 404
```

---

## Migrasjonsnotater

- `src/web/app.py` erstattes av `create_app()`-factory og Blueprint-filer
- `src/web/templates/index.html` oppdateres med HTMX-attributter og inkluderer partials
- `src/web/static/app.js` beholder waveform og Tauri-spesifikk kode; JS-debounce fjernes

---

## Testsjekkliste

```bash
# Start web-UIet
$ uv run samplemind serve

# Åpne i nettleser: http://localhost:5000

# Bekreft at live-søk fungerer (skriv i søkefeltet)
# Bekreft at energi-filter fungerer (velg fra dropdown)
# Bekreft at audio-avspilling fungerer

# Kjør automatiske tester
$ uv run pytest tests/test_web.py -v
```

---

## Feilsøking

**HTMX-forespørsler fungerer ikke**
```html
<!-- Sjekk at HTMX-scriptet er lastet i <head> -->
<script src="https://unpkg.com/htmx.org@2"></script>
```

**SSE stopper etter 30 sekunder**
```python
# Flask har en standard timeout. For lange imports, øk den:
app.config["PERMANENT_SESSION_LIFETIME"] = 3600
# Eller bruk Flask-SSE biblioteket for mer robust SSE-håndtering
```

**Waveform lastes ikke**
```
Sjekk at /audio/<id>-ruten returnerer korrekt MIME-type (audio/wav)
og at filstien i databasen fortsatt eksisterer.
```
