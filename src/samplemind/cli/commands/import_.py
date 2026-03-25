"""Import WAV samples into the library."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from samplemind.analyzer.batch import analyze_batch
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

# All human-readable output goes to stderr so stdout stays clean for Tauri IPC.
console = Console(stderr=True)


def import_samples(
    source: str,
    json_output: bool = False,
    workers: int = 0,
) -> None:
    """Import all WAV files from a folder (recursive), analyze, and store them.

    Args:
        source:      Path to folder containing WAV files (searched recursively).
        json_output: When True, write machine-readable JSON to stdout only.
                     When False, write a Rich table + summary to stderr.
        workers:     Parallel analysis workers.  0 = os.cpu_count() (auto).
    """
    source_path = Path(source)
    if not source_path.is_dir():
        if json_output:
            print(json.dumps({"error": f"Folder not found: {source}", "imported": 0, "errors": 0, "samples": []}))
        else:
            console.print(f"[red]❌ Folder not found:[/red] {source}")
        sys.exit(1)

    wav_files = sorted(source_path.rglob("*.wav"))
    if not wav_files:
        if json_output:
            print(json.dumps({"imported": 0, "errors": 0, "samples": []}))
        else:
            console.print("[yellow]⚠ No WAV files found in folder.[/yellow]")
        return

    init_orm()

    # ── Run analysis (parallel via ProcessPoolExecutor) ──────────────────────
    raw: list[dict]

    if json_output:
        # No progress bar in JSON mode — stdout must be clean JSON only.
        raw = analyze_batch(wav_files, workers=workers)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(
                f"Analysing {len(wav_files)} file(s)…",
                total=len(wav_files),
            )

            def _on_progress(completed: int, _total: int) -> None:
                progress.update(task_id, completed=completed)

            raw = analyze_batch(wav_files, workers=workers, progress_cb=_on_progress)

    # ── Store results ─────────────────────────────────────────────────────────
    imported = 0
    errors = 0
    results: list[dict] = []

    for path, r in zip(wav_files, raw, strict=False):
        if "error" in r:
            errors += 1
            if not json_output:
                console.print(f"  [red]✗[/red] {path.name} — {r['error']}")
            continue

        try:
            data = SampleCreate(
                filename=path.name,
                path=str(path.resolve()),
                bpm=r.get("bpm"),
                key=r.get("key"),
                mood=r.get("mood"),
                energy=r.get("energy"),
                instrument=r.get("instrument"),
            )
            sample = SampleRepository.upsert(data)
            imported += 1
            results.append(
                {
                    "id": sample.id,
                    "filename": path.name,
                    "path": str(path.resolve()),
                    **{k: r[k] for k in ("bpm", "key", "energy", "mood", "instrument") if k in r},
                }
            )
        except Exception as exc:
            errors += 1
            if not json_output:
                console.print(f"  [red]✗[/red] {path.name} — {exc}")

    # ── Output ────────────────────────────────────────────────────────────────
    if json_output:
        # Rust reads this from stdout; schema must stay stable.
        print(json.dumps({"imported": imported, "errors": errors, "samples": results}))
    else:
        _print_results_table(results)
        console.print(
            f"\n[green]✔ Imported {imported} / {len(wav_files)} sample(s)."
            + (f"  [red]{errors} error(s).[/red]" if errors else "") + "[/green]"
        )


def _print_results_table(results: list[dict]) -> None:
    """Print a Rich summary table of imported samples to stderr."""
    if not results:
        return
    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Filename", min_width=30)
    table.add_column("BPM", justify="right", width=7)
    table.add_column("Key", width=8)
    table.add_column("Energy", width=7)
    table.add_column("Mood", width=12)
    table.add_column("Type", width=9)
    for r in results:
        table.add_row(
            r["filename"],
            str(r.get("bpm") or "?"),
            r.get("key") or "",
            r.get("energy") or "",
            r.get("mood") or "",
            r.get("instrument") or "",
        )
    console.print(table)
