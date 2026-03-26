---
type: conditional
pattern: app/**
---

## Tauri/Rust Rules — Active When Editing app/ Files

### Async Tauri commands MUST use owned types

```rust
// CORRECT — owned String, can cross await boundary
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }

// WRONG — &str cannot cross await boundary (compile error)
pub async fn import_folder(path: &str) -> Result<String, String> { ... }
```

### Register new commands in BOTH places

1. `app/src-tauri/src/main.rs` — add to `invoke_handler![ ... ]`
2. `app/src-tauri/capabilities/*.json` — add to the capabilities array

Missing either one → runtime error when `invoke()` is called from the frontend.

### Spawn Python CLI and read stdout (not stderr)

```rust
use std::process::Command;
let output = Command::new("samplemind")
    .args(["import", &path, "--json"])
    .output()
    .map_err(|e| e.to_string())?;
// Parse stdout only — human text goes to stderr
let result: serde_json::Value = serde_json::from_slice(&output.stdout)
    .map_err(|e| e.to_string())?;
```

### Svelte 5 Runes in app/src/

```svelte
<!-- Use Runes syntax, not legacy reactive declarations -->
let count = $state(0);
let doubled = $derived(count * 2);
$effect(() => { console.log(count); });
```

### Cargo clippy must pass

```bash
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
```

No `#[allow(clippy::...)]` suppressions without a comment explaining why.

### Package manager for app/ is pnpm, not npm

```bash
pnpm install          # install deps
pnpm tauri dev        # dev mode (spawns Flask on port 5174)
# NOTE: pnpm tauri build is in the deny list — do not run in Claude Code
```
