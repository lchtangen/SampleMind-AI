# /debug — Debug a SampleMind Issue

Interactive debugger for common SampleMind problems: audio classification, IPC, database,
JWT auth, sidecar socket, import failures, and test failures.

## Arguments

$ARGUMENTS
Required: issue type or description
  classifier <path>    Debug wrong audio classification for a WAV file
  ipc                  Debug Tauri/Python IPC contract (stdout/stderr split)
  db                   Debug database connectivity or schema issues
  jwt                  Debug JWT auth / 401 errors
  sidecar              Debug sidecar socket not responding
  import <folder>      Debug sample import failures
  test <test-id>       Debug a failing pytest test
  Or describe the issue freely in $ARGUMENTS

Examples:
  /debug classifier ~/Music/kick.wav
  /debug jwt
  /debug sidecar
  /debug ipc
  /debug test tests/test_classifier.py::test_classify_energy_high

---

**Issue: classifier <path>**

Step 1 — Extract raw features:
```bash
uv run samplemind analyze "<path>" --json
```

Step 2 — Show all 9 feature values with their classifier implications:
| Feature | Value | Threshold | Classification impact |
|---------|-------|-----------|----------------------|
| rms | ... | <0.015=low, <0.06=mid, ≥0.06=high | energy |
| centroid_norm | ... | >0.15=bright | mood, instrument |
| zcr | ... | >0.1=hihat, <0.08=kick | instrument |
| flatness | ... | >0.2=hihat, >0.1=sfx | instrument |
| rolloff_norm | ... | >0.3=hihat | instrument |
| onset_mean | ... | >0.8=loop, >3.0=aggressive | instrument, mood |
| onset_max | ... | >4.0=kick, >3.0=snare | instrument |
| low_freq_ratio | ... | >0.35=kick, >0.3=bass | instrument |
| duration | ... | >2.0=loop, <0.8=percussive | instrument |

Step 3 — Show which classifier rule fired and why.
Step 4 — Show adjacent rules that almost fired (within 20% of threshold).
Step 5 — Suggest threshold adjustment in `src/samplemind/analyzer/classifier.py`.

**Issue: ipc**

Diagnose stdout/stderr contamination:
```bash
uv run samplemind list --json 2>/dev/null | python -m json.tool
```

If JSON parse fails: "Non-JSON content is being written to stdout. Check for print() statements."

Show grep for problematic prints:
```bash
grep -rn "^print(" src/samplemind/ --include="*.py" | grep -v "test_"
```

Rule: JSON → stdout only. Human text → stderr only. All new CLI commands support --json flag.

**Issue: db**

```bash
uv run python -c "
from samplemind.core.config import get_settings
print('DB URL:', get_settings().database_url)
from samplemind.data.orm import get_engine
engine = get_engine()
print('Engine:', engine)
with engine.connect() as c:
    print('Connection: OK')
    print('Tables:', engine.dialect.get_table_names(c))
"
```

If error: check DB path exists, run `uv run alembic upgrade head`.

**Issue: jwt**

```bash
# Check API is running
curl -sf http://localhost:8000/api/v1/health || echo "FastAPI not running"

# Decode token (no validation — show payload only)
python -c "
import base64, json, sys
token = '<paste_token>'
parts = token.split('.')
payload = json.loads(base64.b64decode(parts[1] + '=='))
print(json.dumps(payload, indent=2))
"
```

Check `exp` field. If expired: use `/auth refresh <refresh_token>`.
Check `SAMPLEMIND_SECRET_KEY` env var is set and matches what the server uses.

**Issue: sidecar**

```bash
ls -la /tmp/samplemind.sock 2>/dev/null || echo "Socket missing"
echo '{"version": 1, "action": "ping"}' | nc -U /tmp/samplemind.sock 2>/dev/null || echo "No response"
ps aux | grep sidecar | grep -v grep
```

Fix: `uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock &`
Check macOS entitlements: `com.apple.security.cs.allow-unsigned-executable-memory`

**Issue: test <test-id>**

```bash
uv run pytest "<test-id>" -v --tb=long -s --no-header
```

Show full traceback. If fixture error, check `tests/conftest.py`.
Common fix: WAV fixture not generating correctly — show the fixture code.

**Free-form issue:**

Read $ARGUMENTS as a natural language description.
Map to the closest debug scenario above and run the appropriate diagnostic steps.

