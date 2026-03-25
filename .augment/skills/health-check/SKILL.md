---
name: health-check
description: Check the health of all running SampleMind services: FastAPI, Flask web UI, and sidecar
---

# Skill: health-check

Check the health of all running SampleMind services: FastAPI, Flask web UI,
sidecar socket, and database connectivity.

## When to use

Use this skill when the user asks to:
- Verify a service is running and responding
- Debug "connection refused" or 502 errors
- Check how many samples are in the library
- Verify the database is accessible and reachable
- Confirm the sidecar socket is alive

## Checks

### FastAPI REST (port 8000)

```bash
curl -sf http://localhost:8000/api/v1/health
# Expected: {"status":"ok"}
```

### Flask web UI (port 5000)

```bash
curl -sf http://localhost:5000/api/status
```

### Flask in Tauri dev mode (port 5174)

```bash
curl -sf http://localhost:5174/api/status
```

### Sidecar socket

```bash
ls -la /tmp/samplemind.sock 2>/dev/null && echo "socket exists" || echo "socket not found"
echo '{"version": 1, "action": "ping"}' | nc -U /tmp/samplemind.sock
```

### Database connectivity

```bash
uv run python -c "from samplemind.data.orm import get_engine; print('DB OK:', get_engine().url)"
```

### Sample count

```bash
uv run samplemind list --json | python -c "import json,sys; d=json.load(sys.stdin); print(f'Samples: {len(d)}')"
```

## Quick diagnosis

| Service down | Fix |
|-------------|-----|
| FastAPI | `uv run samplemind api --reload` |
| Flask | `uv run samplemind serve` |
| Flask (Tauri) | `cd app && pnpm tauri dev` |
| Sidecar | `uv run python src/samplemind/sidecar/server.py &` |
| DB error | `uv run alembic upgrade head` then check `get_settings().database_url` |

## One-liner full check

```bash
echo "=== FastAPI ===" && curl -sf http://localhost:8000/api/v1/health || echo "DOWN"
echo "=== Flask ===" && curl -sf http://localhost:5000/api/status || echo "DOWN"
echo "=== Sidecar ===" && ls /tmp/samplemind.sock 2>/dev/null && echo "UP" || echo "DOWN"
echo "=== DB ===" && uv run python -c "from samplemind.data.orm import get_engine; print('OK:', get_engine().url)"
```

## Key source files

- `src/samplemind/api/main.py` — FastAPI app
- `src/samplemind/web/app.py` — Flask app
- `src/samplemind/sidecar/server.py` — Unix socket sidecar

## Related skills

- `serve` — start the services
- `sidecar` — manage the sidecar process
- `db-inspect` — deeper database inspection

