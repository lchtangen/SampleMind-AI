# /health — Service Health Check

Check the health of all running SampleMind services: FastAPI, Flask, sidecar socket, and database.

## Arguments

$ARGUMENTS
Optional:
  fastapi      Check only FastAPI REST API (port 8000)
  flask        Check only Flask web UI (port 5000)
  sidecar      Check only Unix socket sidecar
  db           Check only database connectivity
  all          Check everything (default)

Examples:
  /health
  /health fastapi
  /health db

---

Parse the target from $ARGUMENTS (default: all).

**Step 1 — FastAPI health (if target is "all" or "fastapi"):**

```bash
curl -sf http://localhost:8000/api/v1/health
```

Expected: `{"status":"ok","version":"x.y.z"}`

If connection refused:
- Show: `❌ FastAPI NOT running (port 8000)`
- Fix: `uv run samplemind api --reload`

If OK: `✓ FastAPI     http://localhost:8000/api/docs`

**Step 2 — Flask health (if target is "all" or "flask"):**

```bash
curl -sf http://localhost:5000/api/status
```

Also check Tauri dev port:
```bash
curl -sf http://localhost:5174/api/status
```

If connection refused:
- Show: `❌ Flask NOT running (port 5000)`
- Fix: `uv run samplemind serve --port 5000`

If OK: `✓ Flask       http://localhost:5000`

**Step 3 — Sidecar socket (if target is "all" or "sidecar"):**

```bash
ls -la /tmp/samplemind.sock 2>/dev/null
```

If socket file exists, ping it:
```bash
echo '{"version": 1, "action": "ping"}' | nc -U /tmp/samplemind.sock 2>/dev/null
```

If missing:
- Show: `❌ Sidecar NOT running (/tmp/samplemind.sock missing)`
- Fix: `uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock &`

If OK: `✓ Sidecar     /tmp/samplemind.sock`

**Step 4 — Database health (if target is "all" or "db"):**

```bash
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import text
with get_engine().connect() as c:
    count = c.execute(text('SELECT COUNT(*) FROM samples')).scalar()
    print(f'DB OK — {count} samples')
"
```

Also check Alembic state:
```bash
uv run alembic current 2>/dev/null || echo "Alembic not configured"
```

If error:
- Show: `❌ Database ERROR`
- Fix: `uv run python -c "from samplemind.data.database import init_db; init_db()"`

If OK: `✓ Database    <count> samples | revision: <alembic_rev>`

**Step 5 — Show final summary table:**

```
Service Health Check — SampleMind-AI
══════════════════════════════════════
✓ FastAPI     http://localhost:8000/api/docs
✓ Flask       http://localhost:5000
❌ Sidecar    /tmp/samplemind.sock not found
✓ Database    247 samples | revision: abc123

Issues found: 1
Fix sidecar: uv run python src/samplemind/sidecar/server.py &
```

