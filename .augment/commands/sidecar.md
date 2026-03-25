# /sidecar — Start Python Sidecar Server

Start the Python sidecar socket server for testing JUCE plugin IPC communication.

## Arguments

$ARGUMENTS
Optional:
  --socket PATH   custom socket path (default: /tmp/samplemind.sock)
  --test          send a ping after starting and show the response
  --stop          stop a running sidecar process

---

Manage the Python sidecar server for JUCE plugin testing. Arguments: $ARGUMENTS

**Step 1 — Check if a sidecar is already running:**
```bash
lsof /tmp/samplemind.sock 2>/dev/null || echo "No sidecar running"
```

**Step 2 — Handle --stop flag:**
If $ARGUMENTS contains --stop:
```bash
pkill -f "samplemind/sidecar/server.py" && echo "Sidecar stopped"
```
Then exit.

**Step 3 — Check Phase 8 sidecar exists:**
Look for `src/samplemind/sidecar/server.py`.
If missing: explain this is Phase 8 work, reference `docs/en/phase-08-vst-plugin.md`.

**Step 4 — Start the sidecar:**
Parse socket path from --socket flag (default: `/tmp/samplemind.sock`).

```bash
# Start in background:
uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock &
echo "Sidecar PID: $!"
sleep 1   # give it time to start
```

**Step 5 — Test the connection (if --test or by default):**
```python
import socket, json, struct
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect('/tmp/samplemind.sock')
    req = json.dumps({'action': 'ping'}).encode()
    s.sendall(struct.pack('>I', len(req)) + req)
    length = struct.unpack('>I', s.recv(4))[0]
    response = json.loads(s.recv(length))
    print(response)
# Expected: {'status': 'ok', 'message': 'SampleMind sidecar running'}
```

Show the response. If ping fails, check for errors in the sidecar output.

**Step 6 — Show available actions:**
Remind the user of the supported socket actions:
- `{"action": "ping"}` — connectivity check
- `{"action": "search", "query": "...", "energy": "...", "instrument": "..."}` — search library
- `{"action": "analyze", "path": "/path/to/file.wav"}` — analyze a file

Show how to stop: `pkill -f "sidecar/server.py"` or re-run `/sidecar --stop`.
