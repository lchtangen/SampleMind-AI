# Phase 4 Agent — CLI

Handles: Typer commands, Rich terminal UX, JSON output contract, watch mode, export, shell completion.

## Triggers
- Phase 4, Typer, Rich, CLI command, JSON output, watch mode, watchdog, export, shell completion

## Key Files
- `src/samplemind/cli/app.py`
- `src/samplemind/cli/commands/`

## CLI Contract (CRITICAL)

```
JSON → stdout ONLY      (machine-readable, parsed by Tauri)
Text → stderr ONLY      (human-readable, never parsed)
```

**Why:** Rust/Tauri parses stdout. Mixing text into stdout silently breaks integration.

## Rules
1. All commands with `--json` flag: `print(json.dumps(...))` to stdout
2. All Rich output: `Console(stderr=True)` — never to stdout
3. `uv run samplemind watch <folder>` requires `uv add watchdog`
4. Shell completion: `app = typer.Typer(add_completion=True)`
5. Export command supports: `fl-studio`, `folder:<path>`, `csv`, `json`, `playlist-m3u`

