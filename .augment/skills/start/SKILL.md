# Skill: start

Start all SampleMind services (Flask + FastAPI) and optionally Tauri dev mode.
Designed as the "good morning" command to get everything running.

## When to use

Use this skill when the user asks to:
- Start everything at once
- Begin a development session
- Start the "dev environment"
- Launch all services in the background

## Quick start (all services)

```bash
# Terminal 1 — Flask web UI
uv run samplemind serve &

# Terminal 2 — FastAPI REST + auth
uv run samplemind api --reload &

# Terminal 3 — Tauri dev mode (optional — wraps Flask at port 5174)
cd app && pnpm tauri dev
```

## Individual services

### Flask web UI (port 5000)

```bash
uv run samplemind serve
```

### FastAPI REST API (port 8000)

```bash
uv run samplemind api --reload
```

### Tauri desktop (dev mode)

```bash
cd app && pnpm tauri dev
```

### Python sidecar (for JUCE plugin testing)

```bash
uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock &
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Flask web UI | http://localhost:5000 | Browse + tag samples |
| FastAPI | http://localhost:8000 | REST API + auth |
| API docs | http://localhost:8000/api/docs | OpenAPI/Swagger |
| Health | http://localhost:8000/api/v1/health | Quick health check |
| Tauri (dev) | http://localhost:5174 | Tauri WebView origin |

## Pre-start checklist

```bash
# 1. Ensure deps are up to date
uv sync --dev

# 2. Ensure DB migrations are applied
uv run alembic upgrade head

# 3. Verify imports work
uv run samplemind --help
```

## Stop all services

```bash
pkill -f "samplemind serve" 2>/dev/null
pkill -f "samplemind api" 2>/dev/null
pkill -f "samplemind/sidecar/server.py" 2>/dev/null
```

## First run after setup

```bash
# Register account (after starting FastAPI)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "you@example.com", "password": "SecurePass1"}'

# Import samples
uv run samplemind import ~/Music/Samples/ --json
```

## Related skills

- `serve` — detailed service management
- `health-check` — verify services are responding
- `setup-dev` — first-time environment setup

