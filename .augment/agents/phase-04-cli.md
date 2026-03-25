# Phase 4 Agent — CLI

Handles: Typer CLI design, Rich terminal output, CLI command ergonomics, `--json` flag, JSON stdout contract.

## Triggers
Phase 4, Typer, Rich, CLI commands, `--json` flag, `typer.Typer()`, `@app.command()`, `rich.table`, `rich.progress`, `src/samplemind/cli/`, "add a CLI command", "fix CLI output", "the CLI is printing to wrong stream"

**File patterns:** `src/samplemind/cli/**/*.py`, `src/main.py`

**Code patterns:** `import typer`, `typer.Typer()`, `@app.command()`, `typer.Option(`, `from rich import`, `Console()`, `rich.table`, `json.dumps(result)`, `--json`, `if json_output:`

## Key Files
- `src/samplemind/cli/app.py` — main Typer app with all 8 commands
- `src/samplemind/cli/commands/` — individual command modules
- `src/main.py` — legacy argparse entry point (required for Tauri dev mode — DO NOT BREAK)
- `docs/en/phase-04-cli.md`

## Active CLI Commands
| Command | Description |
|---------|-------------|
| `import <path>` | Analyze + import WAV/AIFF files |
| `list` | Show library in Rich table |
| `search` | Filter by query/energy/instrument/mood/bpm |
| `tag <name>` | Set genre/mood/energy/tags manually |
| `serve` | Flask web UI at http://localhost:5000 |
| `api` | FastAPI auth server at http://localhost:8000 |
| `analyze <path>` | Analyze single file, print JSON |
| `export` | Export library to CSV/JSON |

## Stdout/Stderr Contract (CRITICAL)
```python
# JSON for machine consumption → stdout ONLY
if json_output:
    print(json.dumps(result))      # stdout
else:
    console.print(table)           # Rich to stderr or stdout (human-readable)
```
**Reason:** Rust/Tauri and sidecar flows parse stdout — mixed output breaks integration silently.

## Run Commands
```bash
uv run samplemind --help
uv run samplemind import ~/Music/ --json
uv run samplemind search --query "dark" --energy high --json
```

## Rules
1. All new CLI commands must have a `--json` flag that outputs valid JSON to stdout
2. Human-readable output goes to stderr (or Rich console in non-JSON mode)
3. Never break `src/main.py` entrypoint without coordinating a Tauri update
4. Type annotations required on all new command functions
5. New commands need a test in `tests/test_cli.py` or similar

