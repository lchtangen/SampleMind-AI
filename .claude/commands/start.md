# /start — Quick-Start Services

Start SampleMind services in the correct order. Validates health after each start.

## Arguments

$ARGUMENTS
Modes:
  web              Flask web UI on port 5000 (default)
  api              FastAPI REST API on port 8000 with auto-reload
  desktop          Tauri desktop app in dev mode (HMR)
  both             Flask + Tauri dev together
  all              Flask + FastAPI + Tauri dev
  --port N         Override Flask port (default 5000)

Examples:
  /start
  /start web --port 5174
  /start api
  /start both
  /start all

---

Parse mode and options from $ARGUMENTS. Default mode: web.

**Step 0 — Pre-flight check:**

Verify environment is set up:
```bash
uv run samplemind --help 2>&1 | head -1
```

If it fails: "Run /setup first to initialize the dev environment."

**Mode: web (or default)**

```bash
uv run samplemind serve --port <port>
```

Wait for startup (poll port):
```bash
timeout 15 bash -c 'until curl -sf http://localhost:<port>/api/status; do sleep 0.5; done'
```

On success:
```
✓ Flask web UI started
  URL:    http://localhost:<port>
  Login:  http://localhost:<port>/login
  API:    http://localhost:<port>/api/samples
  Note:   First run? Register at http://localhost:<port>/register
```

**Mode: api**

```bash
uv run samplemind api --reload
```

Wait and validate:
```bash
timeout 15 bash -c 'until curl -sf http://localhost:8000/api/v1/health; do sleep 0.5; done'
```

On success:
```
✓ FastAPI REST API started
  URL:     http://localhost:8000
  Docs:    http://localhost:8000/api/docs
  Health:  http://localhost:8000/api/v1/health
  Note:    Register first: /auth register <email> <user> <pass>
```

**Mode: desktop**

Pre-check: verify pnpm and cargo are installed:
```bash
pnpm --version && cargo --version
```

If missing: "Install pnpm and Rust first: /setup --full"

```bash
cd app && pnpm tauri dev
```

Note: "Tauri dev mode connects to Flask at http://127.0.0.1:5174 — start Flask on that port first:
`uv run samplemind serve --port 5174`"

**Mode: both**

```bash
# Start Flask on Tauri's port in background
uv run samplemind serve --port 5174 &
FLASK_PID=$!

# Wait for Flask
timeout 15 bash -c 'until curl -sf http://localhost:5174/api/status; do sleep 0.5; done'

# Start Tauri dev (foreground)
cd app && pnpm tauri dev
```

**Mode: all**

Start all three services:
1. FastAPI on 8000 (background)
2. Flask on 5000 (background)
3. Tauri dev (foreground)

**Stop all services:**

```bash
pkill -f "samplemind serve" 2>/dev/null
pkill -f "samplemind api" 2>/dev/null
pkill -f "pnpm tauri" 2>/dev/null
echo "All SampleMind services stopped."
```

**Service port reference:**
- Flask web UI: 5000 (or 5174 for Tauri dev)
- FastAPI REST: 8000
- Tauri Vite HMR: 1420 (auto)
- Sidecar socket: /tmp/samplemind.sock

