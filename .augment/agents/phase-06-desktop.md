# Phase 6 Agent — Desktop App

Handles: Tauri 2 desktop application, Svelte 5 Runes frontend, system tray, IPC bridge, pnpm build.

## Triggers
Phase 6, Tauri desktop app, Svelte 5, system tray, `app/src/`, `app/src-tauri/`, `invoke()`, `$state`, `$derived`, `$effect`, Svelte Runes, TypeScript components, `pnpm tauri dev`, "build the app"

**File patterns:** `app/src/**/*.svelte`, `app/src/**/*.ts`, `app/src-tauri/src/**/*.rs`, `app/src-tauri/tauri.conf.json`, `app/src-tauri/capabilities/**/*.json`

## Key Files
- `app/src/` — Svelte 5 frontend
- `app/src-tauri/src/main.rs` — Rust entry point, tray setup, command registration
- `app/src-tauri/tauri.conf.json` — bundle id, product name, window config
- `app/src-tauri/capabilities/` — Tauri 2 capability definitions
- `app/src-tauri/Cargo.toml` — Rust dependencies
- `docs/en/phase-06-desktop-app.md`

## Svelte 5 Runes (use ONLY these patterns)
```svelte
<script lang="ts">
  let count = $state(0);
  let doubled = $derived(count * 2);
  $effect(() => { console.log('count changed:', count); });
</script>
```

## Tauri IPC Pattern
```typescript
import { invoke } from '@tauri-apps/api/core';
const result = await invoke<string>('import_folder', { path: '/path/to/samples' });
```

## Build Commands
```bash
cd app && pnpm install
pnpm tauri dev         # dev mode (spawns Flask on port 5174)
pnpm tauri build       # production bundle
pnpm tauri build --target universal-apple-darwin   # macOS Universal Binary
```

## Rules
1. Svelte 5 Runes ONLY — no Svelte 4 `$:` reactive declarations
2. Use `pnpm` in `app/` — never `npm`
3. New Tauri commands: register in `invoke_handler!` AND `capabilities/*.json`
4. Async Rust commands must use owned types (String, not &str)
5. `cargo clippy -- -D warnings` must pass before any commit

