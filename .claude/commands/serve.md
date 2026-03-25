# /serve — Start SampleMind Services

Start Flask web UI, FastAPI REST API, or both. Includes health validation.

## Arguments

$ARGUMENTS
Optional:
  web          Start Flask web UI (default, port 5000)
  api          Start FastAPI REST API (port 8000, auto-reload)
  both         Start Flask + FastAPI together
  --port N     Override Flask port (default 5000)
  --reload     Enable uvicorn auto-reload for FastAPI

Examples:
  /serve
  /serve web --port 5174
  /serve api --reload
  /serve both

---

Parse the arguments in $ARGUMENTS for mode (web/api/both) and options.

**Step 1 — Choose mode:**

If mode is `web` or no argument:
```bash
uv run samplemind serve --port <port>
```
Flask starts at http://localhost:<port>
Routes: /, /login, /register, /logout, /api/samples, /api/tag, /api/import, /api/status, /audio/<id>

If mode is `api`:
```bash
uv run samplemind api --reload
```
FastAPI starts at http://localhost:8000
Docs: http://localhost:8000/api/docs
Health: http://localhost:8000/api/v1/health

If mode is `both`:
Start Flask in background, then FastAPI in foreground:
```bash
uv run samplemind serve --port 5000 &
uv run samplemind api --reload
```

**Step 2 — Validate startup:**

For Flask, verify with:
```bash
curl -sf http://localhost:<port>/api/status
```

For FastAPI, verify with:
```bash
curl -sf http://localhost:8000/api/v1/health
```

If health check fails, show the exact error and suggest:
- Check that `uv sync` was run
- Check that DB was initialized: `uv run python -c "from samplemind.data.database import init_db; init_db()"`

**Step 3 — Show service summary:**

Report:
- Flask URL: http://localhost:<port>
- FastAPI URL: http://localhost:8000
- API Docs: http://localhost:8000/api/docs (if API started)
- Tauri dev mode: Use `--port 5174` for Flask when running `pnpm tauri dev`

**Step 4 — Show first-use steps:**

If this is first run (library is empty):
1. Open http://localhost:<port>/register to create an account
2. Import samples: `uv run samplemind import ~/Music/Samples/ --json`
3. Search: http://localhost:<port>

Note: Legacy entrypoint `python src/web/app.py` still works for Tauri dev mode.

