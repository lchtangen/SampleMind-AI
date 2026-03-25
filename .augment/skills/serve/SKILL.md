---
name: serve
description: Start the SampleMind web services: Flask UI, FastAPI REST server, or both
---

# Skill: serve

Start the SampleMind web services — Flask UI, FastAPI REST server, or both.

## When to use

Use this skill when the user asks to:
- Start the web UI to browse the sample library
- Launch the FastAPI server for API/auth endpoints
- Start both services simultaneously
- Run Tauri desktop app in dev mode

## Commands by mode

### Flask web UI (default — port 5000)
```bash
uv run samplemind serve
uv run samplemind serve --port 5174   # for Tauri dev mode
```

### FastAPI REST API (port 8000)
```bash
uv run samplemind api
uv run samplemind api --reload        # auto-reload on code changes
```

### Both simultaneously
```bash
uv run samplemind serve --port 5000 &
uv run samplemind api --reload
```

### Tauri desktop app in dev mode
```bash
cd app && pnpm tauri dev
```

## Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| Flask web UI | http://localhost:5000 | Browse library, search, tag |
| Flask (Tauri) | http://localhost:5174 | Port used by `pnpm tauri dev` |
| FastAPI | http://localhost:8000 | REST API + auth |
| API docs | http://localhost:8000/api/docs | OpenAPI / Swagger UI |
| Health check | http://localhost:8000/api/v1/health | `{"status": "ok"}` |

## Flask routes

| Route | Description |
|-------|-------------|
| `GET /` | Library view (login required) |
| `GET /login` | Login page |
| `GET /register` | Register page |
| `GET /api/samples` | JSON sample list (HTMX live search) |
| `POST /api/tag` | Update sample tags |
| `POST /api/import` | Trigger folder import |
| `GET /api/status` | Health check + library stats |
| `GET /audio/<id>` | Stream WAV for browser playback |

## FastAPI routes

| Route | Description |
|-------|-------------|
| `POST /api/v1/auth/register` | Create account |
| `POST /api/v1/auth/login` | Get JWT token pair |
| `POST /api/v1/auth/refresh` | Refresh access token |
| `GET /api/v1/auth/me` | Current user profile |
| `GET /api/v1/health` | Health check |

## Health validation

After starting Flask:
```bash
curl -sf http://localhost:5000/api/status
```

After starting FastAPI:
```bash
curl -sf http://localhost:8000/api/v1/health
```

If health check fails:
1. Run `uv sync --dev` to ensure all deps are installed
2. Run `uv run alembic upgrade head` to apply DB migrations
3. Check for port conflicts: `lsof -i :5000` or `lsof -i :8000`

## First-run checklist

1. Register an account: open `http://localhost:5000/register`
2. Import samples: `uv run samplemind import ~/Music/Samples/ --json`
3. Search: `uv run samplemind search --query kick --json`

## Notes

- Legacy entry point `python src/web/app.py` still works for Tauri dev mode
- Both Flask and FastAPI can run at the same time on different ports
- Tauri WebView connects to Flask at `http://127.0.0.1:5174` in dev mode

## Related skills

- `import-samples` — load audio files into the library
- `search-library` — query the library via CLI
- `db-migrate` — apply migrations before first run

