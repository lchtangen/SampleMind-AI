---
name: sidecar
description: Manage the Python sidecar server used by the JUCE plugin and Tauri IPC over a Unix socket
---

# Skill: sidecar

Manage the Python sidecar server used by the JUCE plugin and Tauri IPC.
Communicates over a Unix domain socket at `/tmp/samplemind.sock`.

## When to use

Use this skill when the user asks to:
- Start the sidecar server for JUCE plugin testing
- Send a ping or test command to the sidecar
- Stop the running sidecar
- Debug sidecar connectivity issues
- Check the socket IPC protocol

## Commands

### Start (foreground)

```bash
uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock
```

### Start (background)

```bash
uv run python src/samplemind/sidecar/server.py --socket /tmp/samplemind.sock &
```

### Check status

```bash
ls -la /tmp/samplemind.sock 2>/dev/null && echo "socket exists" || echo "socket not found"
```

### Send ping

```bash
echo '{"version": 1, "action": "ping"}' | nc -U /tmp/samplemind.sock
```

### Stop

```bash
pkill -f samplemind/sidecar/server.py
```

## IPC Protocol

Socket path: `/tmp/samplemind.sock` (Unix domain socket)

Request envelope:
```json
{ "version": 1, "action": "<action>", "payload": { ... } }
```

Response envelope:
```json
{ "version": 1, "status": "ok", "data": { ... } }
```

Valid actions: `ping`, `analyze`, `search`, `import`, `status`

⚠ **Protocol changes must bump the `version` field** — never change v1 behavior in place.

## macOS Requirements

Tauri app entitlement required for running the sidecar:
```
com.apple.security.cs.allow-unsigned-executable-memory
```

## JUCE Integration (Phase 8)

The JUCE plugin launches the Python sidecar as a `ChildProcess` and communicates
via the Unix socket. Socket must exist before the plugin loads.

## Debugging

```bash
# Verify sidecar responds
echo '{"version": 1, "action": "ping"}' | nc -U /tmp/samplemind.sock
# Expected: {"version": 1, "status": "ok", "data": {"pong": true}}

# Check for stale socket
ls -la /tmp/samplemind.sock
rm /tmp/samplemind.sock   # if server crashed without cleanup
```

## Key source files

- `src/samplemind/sidecar/server.py` — main sidecar process
- `plugin/Source/PluginProcessor.cpp` — JUCE plugin that connects to socket

## Related skills

- `health-check` — check if socket is alive
- `build` — build the JUCE plugin that connects to the sidecar

