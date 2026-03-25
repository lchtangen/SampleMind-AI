# Memory: IPC Contract

The stdout/stderr split is a critical invariant. Violating it breaks Tauri IPC silently.

## The Rule

| Stream | Content | Who reads it |
|--------|---------|-------------|
| **stdout** | JSON only — machine-readable | Tauri (`Command::output()`), sidecar, tests |
| **stderr** | Human text, Rich progress bars | Terminal, developer |

## CLI Pattern (Typer commands)

```python
import sys, json, typer

@app.command()
def import_cmd(folder: Path, json_output: bool = typer.Option(False, "--json")):
    # Progress → stderr (Rich)
    typer.echo(f"Scanning {folder}...", err=True)

    # Result → stdout (JSON only when --json)
    if json_output:
        print(json.dumps({"imported": count, "errors": errors}))
    else:
        typer.echo(f"✓ Imported {count} samples", err=False)
```

## Tauri Rust Consumer Pattern

```rust
use std::process::Command;
let output = Command::new("samplemind")
    .args(["import", &path, "--json"])
    .output()
    .map_err(|e| e.to_string())?;
// Parse stdout only — stderr contains human text
let result: serde_json::Value = serde_json::from_slice(&output.stdout)?;
```

## Sidecar Socket Protocol

Unix domain socket at `/tmp/samplemind.sock`. JSON envelope format:

```json
{ "version": 1, "action": "analyze", "payload": { "path": "/abs/path.wav" } }
```

Response:
```json
{ "version": 1, "status": "ok", "data": { ... feature dict ... } }
```

**⚠ Protocol changes must bump the `version` field** — never change v1 in place.

Valid actions: `ping`, `analyze`, `search`, `import`, `status`

## FastAPI Auth Token Header

```http
Authorization: Bearer <access_token>
```

Access token = JWT (HS256, 30 min). Refresh token = opaque (7 days).
Secret from `SAMPLEMIND_SECRET_KEY` env var — **never hardcode**.

## Tauri Async Command Contract

```rust
// Owned types only across await boundaries:
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }
// Register in BOTH invoke_handler![] AND capabilities/<name>.json
```

