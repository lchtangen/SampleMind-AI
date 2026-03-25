# Phase 6 Agent — Desktop App

Handles: Tauri 2, Rust commands, Svelte 5 Runes, system tray, global shortcuts, drag-to-DAW.

## Triggers
- Phase 6, Tauri, Rust, Svelte 5 Runes, IPC, system tray, global shortcut, drag to DAW, desktop

## Key Files
- `app/src-tauri/src/`
- `app/src/`
- `app/src-tauri/tauri.conf.json`
- `app/src-tauri/capabilities/`

## Critical Patterns

```rust
// CORRECT — owned String for async commands
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }

// WRONG — &str cannot cross await boundary
pub async fn import_folder(path: &str) -> Result<String, String> { ... }
```

## Svelte 5 Runes Pattern

```svelte
<script lang="ts">
  let query = $state('');
  let results = $derived(query ? search(query) : []);
</script>
```

## Rules
1. Async commands: owned `String`, not `&str`
2. New Tauri commands: register in `invoke_handler!` AND `capabilities/*.json`
3. `cargo clippy -- -D warnings` must pass before any commit
4. Use `pnpm` in `app/` — never `npm`
5. System tray: `tauri-plugin-tray`, global shortcuts: `tauri-plugin-global-shortcut`
6. Drag-to-DAW: `tauri-plugin-drag`, `DragItem::Files(vec![path])`

