# Phase 5 Agent — Web UI

Handles: Flask web UI architecture, HTMX interactions, SSE progress streams, session-based auth, audio streaming.

## Triggers
Phase 5, Flask web UI, HTMX, SSE progress, `/api/samples` live search, `/api/import` progress, session auth, Flask-Login, audio streaming, Jinja2 templating, "add a web feature", "fix the web UI", "HTMX not updating"

**File patterns:** `src/samplemind/web/app.py`, `src/web/app.py`, `src/samplemind/web/templates/**/*.html`, `src/samplemind/web/static/**`

## Key Files
- `src/samplemind/web/app.py` — new src-layout Flask app
- `src/web/app.py` — legacy Flask app (Tauri dev mode proxy — do not break)
- `src/samplemind/web/templates/` — Jinja2 templates (base, index, login, register)
- `src/samplemind/web/static/` — CSS, JS, audio player
- `docs/en/phase-05-web.md`

## Flask Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Library view (HTMX live search) |
| `/login` | GET/POST | Session login |
| `/register` | GET/POST | User registration |
| `/api/samples` | GET | JSON samples (HTMX target) |
| `/api/import` | POST | SSE import progress stream |
| `/api/tag` | POST | Update sample tags |
| `/audio/<id>` | GET | Stream audio file |

## Run Command
```bash
uv run samplemind serve     # http://localhost:5000
```

## Rules
1. Keep API response shapes stable — Tauri/desktop consumers depend on them
2. Prefer additive API changes over breaking changes
3. `flask-cors` required for Tauri WebView cross-origin requests
4. Audio streaming must use `send_file` with correct MIME (`audio/wav`)
5. Session auth (Flask) is separate from JWT auth (FastAPI) — never mix them
6. Never break `src/web/app.py` without a coordinated Tauri update

