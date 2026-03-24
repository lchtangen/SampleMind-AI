# Phase 4 — CLI with Typer and Rich

> Replace the `argparse`-based `main.py` with a modern **Typer** CLI that provides automatic
> `--help`, type validation, Rich-formatted output, and a JSON mode for Tauri IPC.

---

## Prerequisites

- Phases 1–3 complete
- `typer` and `rich` in `pyproject.toml`
- Basic familiarity with Python functions and type annotations

---

## Goal State

- `src/samplemind/cli/app.py` with Typer replacing `src/main.py`
- All 6 commands migrated: `import`, `analyze`, `list`, `search`, `tag`, `serve`
- All commands support `--json` for machine-readable output
- Rich progress bar during import and batch analysis
- `samplemind --help` works directly from the terminal
- Tauri IPC contract documented

---

## 1. Why Typer?

Typer uses Python's type annotations to generate a complete CLI automatically:

```python
# argparse (old) — lots of boilerplate
parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)
p = sub.add_parser("import")
p.add_argument("source", help="Folder with WAV files")
args = parser.parse_args()

# Typer (new) — clean and readable
import typer
app = typer.Typer()

@app.command()
def import_(source: Path):
    """Import WAV samples into the library."""
    ...
```

Advantages:
- Automatic `--help` from docstrings
- Type validation (Typer raises an error if the user provides the wrong type)
- Shell completion with `samplemind --install-completion`
- Easy to test with `typer.testing.CliRunner`

---

## 2. App Structure

```
src/samplemind/cli/
├── __init__.py
├── app.py              ← Main Typer app (registers all commands)
└── commands/
    ├── __init__.py
    ├── import_.py      ← import command (underscore: avoids Python keyword)
    ├── analyze.py      ← analyze command
    ├── search.py       ← list and search commands
    ├── tag.py          ← tag command
    └── serve.py        ← serve command
```

---

## 3. Main App — app.py

```python
# filename: src/samplemind/cli/app.py

import typer
from samplemind.cli.commands import import_, analyze, search, tag, serve

# Create main app
app = typer.Typer(
    name="samplemind",
    help="AI-driven sample library for FL Studio",
    add_completion=True,   # Enable shell completion
    rich_markup_mode="rich",
)

# Register all subcommands
app.command("import")(import_.import_cmd)
app.command("analyze")(analyze.analyze_cmd)
app.command("list")(search.list_cmd)
app.command("search")(search.search_cmd)
app.command("tag")(tag.tag_cmd)
app.command("serve")(serve.serve_cmd)


if __name__ == "__main__":
    app()
```

---

## 4. The import Command with Rich and JSON Mode

```python
# filename: src/samplemind/cli/commands/import_.py

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository
from samplemind.models import SampleCreate

# Use stderr for status messages, stdout for data (JSON)
# This is critical for Tauri IPC — Rust reads stdout, not stderr
console = Console(stderr=True)
stdout = Console(force_terminal=False)   # No ANSI codes in JSON output


def import_cmd(
    source: Path = typer.Argument(..., help="Folder with WAV files to import"),
    json_output: bool = typer.Option(False, "--json", help="Return JSON instead of table"),
    workers: int = typer.Option(4, "--workers", "-w", help="Number of parallel analysis jobs"),
):
    """
    Import WAV samples from a folder into the library.
    Automatically analyses BPM, key, energy, mood, and instrument type.
    """
    if not source.is_dir():
        console.print(f"[red]Error: Folder not found: {source}[/red]")
        raise typer.Exit(1)

    wav_files = list(source.glob("**/*.wav"))
    if not wav_files:
        console.print("[yellow]No WAV files found.[/yellow]")
        raise typer.Exit(0)

    init_db()
    repo = SampleRepository()
    results = []

    # Rich progress bar (shown only when NOT --json)
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=json_output,   # Hide progress in JSON mode
    ) as progress:
        task = progress.add_task(f"Analysing {len(wav_files)} files...", total=len(wav_files))

        for wav in wav_files:
            try:
                analysis = analyze_file(str(wav))
                data = SampleCreate(
                    filename=wav.name,
                    path=str(wav.resolve()),
                    **analysis,
                )
                sample = repo.upsert(data)
                results.append({"id": sample.id, "filename": sample.filename, **analysis})
            except Exception as e:
                console.print(f"[red]Error: {wav.name} — {e}[/red]")
            finally:
                progress.advance(task)

    # Output: JSON to stdout (for Tauri), table to stderr (for humans)
    if json_output:
        # Rust reads this from stdout via Command::new("samplemind")
        print(json.dumps({"imported": len(results), "samples": results}))
    else:
        _print_results_table(results, console)
        console.print(f"\n[green]✔ Imported {len(results)} / {len(wav_files)} samples.[/green]")


def _print_results_table(results: list[dict], console: Console):
    """Print results as a Rich table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Filename", min_width=30)
    table.add_column("BPM", justify="right", width=7)
    table.add_column("Key", width=8)
    table.add_column("Energy", width=7)
    table.add_column("Mood", width=12)
    table.add_column("Type", width=8)

    for r in results:
        table.add_row(
            r["filename"],
            str(r.get("bpm", "?")),
            r.get("key", "?"),
            r.get("energy", "?"),
            r.get("mood", "?"),
            r.get("instrument", "?"),
        )
    console.print(table)
```

---

## 5. The search Command

```python
# filename: src/samplemind/cli/commands/search.py

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository

console = Console(stderr=True)


def search_cmd(
    query: Optional[str] = typer.Argument(None, help="Partial filename or tag"),
    key: Optional[str] = typer.Option(None, "--key", help="Key, e.g. 'C maj'"),
    genre: Optional[str] = typer.Option(None, "--genre", help="Genre, e.g. 'trap'"),
    energy: Optional[str] = typer.Option(None, "--energy", help="Energy level: low, mid, high"),
    instrument: Optional[str] = typer.Option(None, "--instrument",
                                              help="Instrument type: kick, snare, bass..."),
    bpm_min: Optional[float] = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: Optional[float] = typer.Option(None, "--bpm-max", help="Maximum BPM"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
):
    """Search the sample library with one or more filters."""
    init_db()
    repo = SampleRepository()
    results = repo.search(
        query=query, key=key, genre=genre, energy=energy,
        instrument=instrument, bpm_min=bpm_min, bpm_max=bpm_max,
    )

    if json_output:
        # Output format used by Tauri frontend
        data = [
            {
                "id": s.id, "filename": s.filename, "path": s.path,
                "bpm": s.bpm, "key": s.key, "mood": s.mood,
                "energy": s.energy, "instrument": s.instrument,
                "genre": s.genre, "tags": s.tags,
            }
            for s in results
        ]
        print(json.dumps(data))
        return

    if not results:
        console.print("[yellow]No samples matched your filter.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=4)
    table.add_column("Filename", min_width=28)
    table.add_column("BPM", width=7, justify="right")
    table.add_column("Key", width=8)
    table.add_column("Type", width=8)
    table.add_column("Genre", width=10)
    table.add_column("Energy", width=7)
    table.add_column("Mood", width=10)

    for i, s in enumerate(results, 1):
        table.add_row(
            str(i), s.filename, str(s.bpm or "?"),
            s.key or "", s.instrument or "",
            s.genre or "", s.energy or "", s.mood or "",
        )
    console.print(table)
    console.print(f"\n{len(results)} result(s) | {repo.count()} total")


def list_cmd(
    key: Optional[str] = typer.Option(None, "--key"),
    bpm_min: Optional[float] = typer.Option(None, "--bpm-min"),
    bpm_max: Optional[float] = typer.Option(None, "--bpm-max"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List all samples in the library."""
    return search_cmd(key=key, bpm_min=bpm_min, bpm_max=bpm_max, json_output=json_output)
```

---

## 6. The tag Command

```python
# filename: src/samplemind/cli/commands/tag.py

from typing import Optional
import typer
from rich.console import Console
from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository
from samplemind.models import SampleUpdate

console = Console()


def tag_cmd(
    name: str = typer.Argument(..., help="Partial filename to identify the sample"),
    genre: Optional[str] = typer.Option(None, "--genre", help="Genre, e.g. 'trap'"),
    mood: Optional[str] = typer.Option(None, "--mood", help="Mood"),
    energy: Optional[str] = typer.Option(None, "--energy", help="Energy: low, mid, or high"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated free tags"),
):
    """Tag a sample with genre, mood, energy, or custom tags."""
    init_db()

    if energy and energy not in {"low", "mid", "high"}:
        console.print(f"[red]Invalid energy '{energy}'. Choose: low, mid, high[/red]")
        raise typer.Exit(1)

    repo = SampleRepository()
    sample = repo.get_by_name(name)

    if not sample:
        console.print(f"[red]No sample matches '{name}'. Run 'samplemind list' to see what's imported.[/red]")
        raise typer.Exit(1)

    update = SampleUpdate(genre=genre, mood=mood, energy=energy, tags=tags)
    repo.tag(sample.path, update)

    console.print(f"[green]Tagged:[/green] {sample.filename}")
    if genre:  console.print(f"  Genre:  {genre}")
    if mood:   console.print(f"  Mood:   {mood}")
    if energy: console.print(f"  Energy: {energy}")
    if tags:   console.print(f"  Tags:   {tags}")
```

---

## 7. The serve Command

```python
# filename: src/samplemind/cli/commands/serve.py

import typer
from rich.console import Console

console = Console()


def serve_cmd(
    port: int = typer.Option(5000, "--port", "-p", help="Port for the web UI"),
    debug: bool = typer.Option(False, "--debug", help="Flask debug mode"),
):
    """Start the web UI at localhost."""
    from samplemind.web.app import create_app
    from samplemind.data.db import init_db

    init_db()
    app = create_app()

    console.print(f"[bold green]SampleMind AI Web UI → http://localhost:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    app.run(debug=debug, port=port)
```

---

## 8. The Tauri IPC Contract

The Rust backend calls `samplemind` as a subprocess and reads JSON from stdout:

```rust
// filename: app/src-tauri/src/commands/import.rs

use std::process::Command;
use serde::Deserialize;

#[derive(Deserialize)]
struct ImportResult {
    imported: usize,
    samples: Vec<SampleJson>,
}

#[derive(Deserialize)]
struct SampleJson {
    id: i64,
    filename: String,
    bpm: Option<f64>,
    key: Option<String>,
    energy: Option<String>,
    mood: Option<String>,
    instrument: Option<String>,
}

/// Call the Python CLI and parse JSON output
#[tauri::command]
pub async fn import_folder(path: String) -> Result<ImportResult, String> {
    let output = Command::new("samplemind")
        .args(["import", &path, "--json"])
        .output()
        .map_err(|e| format!("Could not start samplemind: {}", e))?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        return Err(format!("samplemind import failed: {}", err));
    }

    // Parse JSON from stdout
    serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Invalid JSON from samplemind: {}", e))
}
```

JSON format Rust expects from `samplemind import --json`:

```json
{
  "imported": 3,
  "samples": [
    {
      "id": 1,
      "filename": "kick_128.wav",
      "bpm": 128.0,
      "key": "C maj",
      "energy": "high",
      "mood": "aggressive",
      "instrument": "kick"
    }
  ]
}
```

---

## 9. Testing with CliRunner

```python
# filename: tests/test_cli.py

from typer.testing import CliRunner
from samplemind.cli.app import app
import json
import soundfile as sf
import numpy as np

runner = CliRunner()


def test_import_json_output(tmp_path):
    """import --json should return valid JSON with imported samples."""
    # Create a test WAV file
    y = np.zeros(22050, dtype=np.float32)
    wav = tmp_path / "test.wav"
    sf.write(str(wav), y, 22050)

    result = runner.invoke(app, ["import", str(tmp_path), "--json"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert "imported" in data
    assert "samples" in data
    assert isinstance(data["samples"], list)


def test_import_nonexistent_folder():
    """import with non-existent folder should give exit code 1."""
    result = runner.invoke(app, ["import", "/does/not/exist"])
    assert result.exit_code == 1


def test_search_json_output():
    """search --json should return a list of samples."""
    result = runner.invoke(app, ["search", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_tag_invalid_energy():
    """tag with invalid energy value should give exit code 1."""
    result = runner.invoke(app, ["tag", "kick", "--energy", "ultra"])
    assert result.exit_code == 1
```

---

## 10. Shell Completion

After installation you can enable tab completion for bash/zsh/fish:

```bash
# Bash
$ samplemind --install-completion bash
$ source ~/.bashrc

# Zsh
$ samplemind --install-completion zsh
$ source ~/.zshrc

# Fish
$ samplemind --install-completion fish
```

---

## Migration Notes

- `src/main.py` can be deleted after `cli/app.py` is complete and tested
- `src/cli/analyze.py`, `importer.py`, `library.py`, `tagger.py` are replaced by `cli/commands/`
- Entry point in `pyproject.toml` points to `samplemind.cli.app:app`

---

## Testing Checklist

```bash
# Confirm the samplemind command works
$ uv run samplemind --help

# Test all commands manually
$ uv run samplemind import ~/Music/test-samples/
$ uv run samplemind search --energy high --json
$ uv run samplemind list --bpm-min 120 --bpm-max 140

# Run automated tests
$ uv run pytest tests/test_cli.py -v

# Check shell completion
$ uv run samplemind --install-completion bash
```

---

## Troubleshooting

**Error: `samplemind: command not found`**
```bash
# Reinstall in editable mode:
$ uv pip install -e .
# Or check that pyproject.toml has [project.scripts]
```

**Error: Empty JSON output**
```
Make sure you use print(json.dumps(...)) (not console.print_json())
for JSON output. console writes to stderr, print writes to stdout.
The Rust backend only reads stdout.
```

**Error: Rich colours inside JSON**
```python
# Set force_terminal=False for the stdout Console:
stdout = Console(force_terminal=False)
# This prevents ANSI escape codes in JSON output
```
