# Fase 4 — CLI med Typer og Rich

> Erstatt `argparse`-basert `main.py` med en moderne **Typer**-CLI som gir automatisk `--help`,
> type-validering, Rich-formatert output og JSON-modus for Tauri IPC.

---

## Forutsetninger

- Fase 1–3 fullført
- `typer` og `rich` i `pyproject.toml`
- Grunnleggende kjennskap til Python-funksjoner og type-annotasjoner

---

## Mål etter denne fasen

- `src/samplemind/cli/app.py` med Typer som erstatter `src/main.py`
- Alle 6 kommandoer migrert: `import`, `analyze`, `list`, `search`, `tag`, `serve`
- Alle kommandoer støtter `--json` for maskinlesbart output
- Rich progress-bar under import og batch-analyse
- `samplemind --help` fungerer direkte fra terminalen
- IPC-kontrakt med Tauri dokumentert

---

## 1. Hvorfor Typer?

Typer bruker Pythons type-annotasjoner til å generere et fullstendig CLI automatisk:

```python
# argparse (gammelt) — mye boilerplate
parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)
p = sub.add_parser("import")
p.add_argument("source", help="Mappe med WAV-filer")
args = parser.parse_args()

# Typer (nytt) — rent og lesbart
import typer
app = typer.Typer()

@app.command()
def import_(source: Path):
    """Importer WAV-samples inn i biblioteket."""
    ...
```

Fordeler:
- Automatisk `--help` fra docstrings
- Type-validering (Typer kaster feil hvis bruker gir feil type)
- Shell-komplettering med `samplemind --install-completion`
- Enkelt å teste med `typer.testing.CliRunner`

---

## 2. App-struktur

```
src/samplemind/cli/
├── __init__.py
├── app.py              ← Hoved Typer-app (registrerer alle kommandoer)
└── commands/
    ├── __init__.py
    ├── import_.py      ← import-kommandoen (understrek: unngår Python-keyword)
    ├── analyze.py      ← analyze-kommandoen
    ├── search.py       ← list og search-kommandoene
    ├── tag.py          ← tag-kommandoen
    └── serve.py        ← serve-kommandoen
```

---

## 3. Hoved-app — app.py

```python
# filename: src/samplemind/cli/app.py

import typer
from samplemind.cli.commands import import_, analyze, search, tag, serve

# Opprett hoved-app
app = typer.Typer(
    name="samplemind",
    help="AI-drevet sample-bibliotek for FL Studio",
    add_completion=True,   # Aktiver shell-komplettering
    rich_markup_mode="rich",
)

# Registrer alle underkommandoer
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

## 4. import-kommandoen med Rich og JSON-modus

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
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

# Bruk stderr for status-meldinger, stdout for data (JSON)
# Dette er kritisk for Tauri IPC — Rust leser stdout, ikke stderr
console = Console(stderr=True)
stdout = Console()


def import_cmd(
    source: Path = typer.Argument(..., help="Mappe med WAV-filer å importere"),
    json_output: bool = typer.Option(False, "--json", help="Returner JSON i stedet for tabell"),
    workers: int = typer.Option(4, "--workers", "-w", help="Antall parallelle analysejobber"),
):
    """
    Importer WAV-samples fra en mappe inn i biblioteket.
    Analyserer BPM, toneart, energi, stemning og instrument-type automatisk.
    """
    if not source.is_dir():
        console.print(f"[red]Feil: Mappen finnes ikke: {source}[/red]")
        raise typer.Exit(1)

    wav_files = list(source.glob("**/*.wav"))
    if not wav_files:
        console.print("[yellow]Ingen WAV-filer funnet.[/yellow]")
        raise typer.Exit(0)

    init_orm()
    results = []

    # Rich progress-bar (vises kun når IKKE --json er satt)
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=json_output,   # Skjul progress i JSON-modus
    ) as progress:
        task = progress.add_task(f"Analyserer {len(wav_files)} filer...", total=len(wav_files))

        for wav in wav_files:
            try:
                analysis = analyze_file(str(wav))
                data = SampleCreate(
                    filename=wav.name,
                    path=str(wav.resolve()),
                    **analysis,
                )
                sample = SampleRepository.upsert(data)
                results.append({"id": sample.id, "filename": sample.filename, **analysis})
            except Exception as e:
                console.print(f"[red]Feil: {wav.name} — {e}[/red]")
            finally:
                progress.advance(task)

    # Output: JSON til stdout (for Tauri), tabell til stderr (for mennesker)
    if json_output:
        # Rust leser dette fra stdout via Command::new("samplemind")
        stdout.print_json(json.dumps({"imported": len(results), "samples": results}))
    else:
        _print_results_table(results, console)
        console.print(f"\n[green]✔ Importerte {len(results)} / {len(wav_files)} samples.[/green]")


def _print_results_table(results: list[dict], console: Console):
    """Skriv ut resultater som en Rich-tabell."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Filnavn", min_width=30)
    table.add_column("BPM", justify="right", width=7)
    table.add_column("Toneart", width=8)
    table.add_column("Energi", width=7)
    table.add_column("Stemning", width=12)
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

## 5. search-kommandoen

```python
# filename: src/samplemind/cli/commands/search.py

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

console = Console(stderr=True)
stdout = Console()


def search_cmd(
    query: Optional[str] = typer.Argument(None, help="Delvis filnavn eller tag"),
    key: Optional[str] = typer.Option(None, "--key", help="Toneart, f.eks. 'C maj'"),
    genre: Optional[str] = typer.Option(None, "--genre", help="Sjanger, f.eks. 'trap'"),
    energy: Optional[str] = typer.Option(None, "--energy",
                                          help="Energinivå: low, mid, high"),
    instrument: Optional[str] = typer.Option(None, "--instrument",
                                              help="Instrumenttype: kick, snare, bass..."),
    bpm_min: Optional[float] = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: Optional[float] = typer.Option(None, "--bpm-max", help="Maksimum BPM"),
    json_output: bool = typer.Option(False, "--json", help="JSON-output"),
):
    """Søk i sample-biblioteket med ett eller flere filtre."""
    init_orm()
    results = SampleRepository.search(
        query=query, key=key, genre=genre, energy=energy,
        instrument=instrument, bpm_min=bpm_min, bpm_max=bpm_max,
    )

    if json_output:
        # Output-format brukt av Tauri-frontend
        data = [
            {
                "id": s.id, "filename": s.filename, "path": s.path,
                "bpm": s.bpm, "key": s.key, "mood": s.mood,
                "energy": s.energy, "instrument": s.instrument,
                "genre": s.genre, "tags": s.tags,
            }
            for s in results
        ]
        stdout.print_json(json.dumps(data))
        return

    if not results:
        console.print("[yellow]Ingen samples matchet filteret ditt.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=4)
    table.add_column("Filnavn", min_width=28)
    table.add_column("BPM", width=7, justify="right")
    table.add_column("Toneart", width=8)
    table.add_column("Type", width=8)
    table.add_column("Sjanger", width=10)
    table.add_column("Energi", width=7)
    table.add_column("Stemning", width=10)

    for i, s in enumerate(results, 1):
        table.add_row(
            str(i), s.filename, str(s.bpm or "?"),
            s.key or "", s.instrument or "",
            s.genre or "", s.energy or "", s.mood or "",
        )
    console.print(table)
    console.print(f"\n{len(results)} resultat(er) | {SampleRepository.count()} totalt")


def list_cmd(
    key: Optional[str] = typer.Option(None, "--key"),
    bpm_min: Optional[float] = typer.Option(None, "--bpm-min"),
    bpm_max: Optional[float] = typer.Option(None, "--bpm-max"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List alle samples i biblioteket."""
    return search_cmd(key=key, bpm_min=bpm_min, bpm_max=bpm_max, json_output=json_output)
```

---

## 6. tag-kommandoen

```python
# filename: src/samplemind/cli/commands/tag.py

from typing import Optional
import typer
from rich.console import Console
from samplemind.core.models.sample import SampleUpdate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

console = Console()


def tag_cmd(
    name: str = typer.Argument(..., help="Delvis filnavn for å identifisere samplet"),
    genre: Optional[str] = typer.Option(None, "--genre", help="Sjanger, f.eks. 'trap'"),
    mood: Optional[str] = typer.Option(None, "--mood", help="Stemning"),
    energy: Optional[str] = typer.Option(None, "--energy",
                                          help="Energi: low, mid eller high"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Kommaseparerte frie tags"),
):
    """Tag et sample med sjanger, stemning, energi eller egendefinerte tags."""
    init_orm()

    if energy and energy not in {"low", "mid", "high"}:
        console.print(f"[red]Ugyldig energi '{energy}'. Velg: low, mid, high[/red]")
        raise typer.Exit(1)

    sample = SampleRepository.get_by_name(name)

    if not sample:
        console.print(f"[red]Ingen sample matcher '{name}'. Kjør 'samplemind list' for å se hva som er importert.[/red]")
        raise typer.Exit(1)

    update = SampleUpdate(genre=genre, mood=mood, energy=energy, tags=tags)
    SampleRepository.tag(sample.path, update)

    console.print(f"[green]Tagget:[/green] {sample.filename}")
    if genre:  console.print(f"  Sjanger:  {genre}")
    if mood:   console.print(f"  Stemning: {mood}")
    if energy: console.print(f"  Energi:   {energy}")
    if tags:   console.print(f"  Tags:     {tags}")
```

---

## 7. serve-kommandoen

```python
# filename: src/samplemind/cli/commands/serve.py

import typer
from rich.console import Console

console = Console()


def serve_cmd(
    port: int = typer.Option(5000, "--port", "-p", help="Porten web-UIet kjører på"),
    debug: bool = typer.Option(False, "--debug", help="Flask debug-modus"),
):
    """Start web-UIet på localhost."""
    from samplemind.data.orm import init_orm
    from samplemind.web.app import create_app

    init_orm()
    app = create_app()

    console.print(f"[bold green]SampleMind AI Web UI → http://localhost:{port}[/bold green]")
    console.print("[dim]Trykk Ctrl+C for å stoppe[/dim]")
    app.run(debug=debug, port=port)
```

---

## 8. Tauri IPC-kontrakten

Rust-backend kaller `samplemind` som en subprocess og leser JSON fra stdout:

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

/// Kall Python CLI og parse JSON-output
#[tauri::command]
pub async fn import_folder(path: String) -> Result<ImportResult, String> {
    let output = Command::new("samplemind")
        .args(["import", &path, "--json"])
        .output()
        .map_err(|e| format!("Kunne ikke starte samplemind: {}", e))?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        return Err(format!("samplemind import feilet: {}", err));
    }

    // Parse JSON fra stdout
    serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Ugyldig JSON fra samplemind: {}", e))
}
```

JSON-format som Rust forventer fra `samplemind import --json`:

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

## 9. Testing med CliRunner

```python
# filename: tests/test_cli.py

from typer.testing import CliRunner
from samplemind.cli.app import app
import json
import soundfile as sf
import numpy as np

runner = CliRunner()


def test_import_json_output(tmp_path):
    """import --json skal returnere gyldig JSON med importerte samples."""
    # Lag en test-WAV-fil
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
    """import med ikke-eksisterende mappe skal gi exit code 1."""
    result = runner.invoke(app, ["import", "/finnes/ikke"])
    assert result.exit_code == 1


def test_search_json_output(tmp_path):
    """search --json skal returnere en liste av samples."""
    result = runner.invoke(app, ["search", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_tag_invalid_energy():
    """tag med ugyldig energi-verdi skal gi exit code 1."""
    result = runner.invoke(app, ["tag", "kick", "--energy", "ultra"])
    assert result.exit_code == 1
```

---

## 10. Shell-komplettering

Etter installasjon kan du aktivere autofullføring for bash/zsh/fish:

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

## Migrasjonsnotater

- `src/main.py` kan slettes etter at `cli/app.py` er ferdig og testet
- `src/cli/analyze.py`, `importer.py`, `library.py`, `tagger.py` erstattes av `cli/commands/`
- Entry point i `pyproject.toml` peker til `samplemind.cli.app:app`

---

## Testsjekkliste

```bash
# Bekreft at samplemind-kommandoen fungerer
$ uv run samplemind --help

# Test alle kommandoer manuelt
$ uv run samplemind import ~/Music/test-samples/
$ uv run samplemind search --energy high --json
$ uv run samplemind list --bpm-min 120 --bpm-max 140

# Kjør automatiske tester
$ uv run pytest tests/test_cli.py -v

# Sjekk shell-komplettering
$ uv run samplemind --install-completion bash
```

---

## Feilsøking

**Feil: `samplemind: command not found`**
```bash
# Reinstaller i redigerbart modus:
$ uv pip install -e .
# Eller sjekk at pyproject.toml har [project.scripts]
```

**Feil: Tomt JSON-output**
```
Sjekk at du bruker stdout.print_json() (ikke console.print_json())
for JSON-output. console skriver til stderr, stdout skriver til stdout.
Rust-backend leser kun stdout.
```

**Feil: Rich-farger i JSON**
```python
# Sett force_terminal=False for stdout Console:
stdout = Console(force_terminal=False)
# Dette forhindrer ANSI-escape-koder i JSON-output
```
