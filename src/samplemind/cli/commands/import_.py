"""Import WAV samples into the library."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from samplemind.analyzer.batch import analyze_batch
from samplemind.core.models.sample import SampleCreate, SampleUpdate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

# All human-readable output goes to stderr so stdout stays clean for Tauri IPC.
console = Console(stderr=True)


def import_samples(
    source: str,
    json_output: bool = False,
    workers: int = 0,
    auto_tag: bool = False,
    deduplicate: bool = False,
) -> None:
    """Import all WAV files from a folder (recursive), analyze, and store them.

    Args:
        source:      Path to folder containing WAV files (searched recursively).
        json_output: When True, write machine-readable JSON to stdout only.
                     When False, write a Rich table + summary to stderr.
        workers:     Parallel analysis workers.  0 = os.cpu_count() (auto).
        auto_tag:    Auto-tag samples via LocalAIEngine (rule-based fallback).
        deduplicate: Skip files whose SHA-256 fingerprint already exists.
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
            print(json.dumps({"imported": 0, "errors": 0, "skipped": 0, "samples": []}))
        else:
            console.print("[yellow]⚠ No WAV files found in folder.[/yellow]")
        return

    init_orm()

    # ── Deduplicate: filter out files already in the library ─────────────────
    skipped = 0
    if deduplicate:
        filtered: list[Path] = []
        for p in wav_files:
            if SampleRepository.get_by_path(str(p.resolve())) is not None:
                skipped += 1
            else:
                filtered.append(p)
        if not json_output and skipped:
            console.print(f"[dim]⏭ Skipping {skipped} already-imported file(s).[/dim]")
        wav_files = filtered

    if not wav_files:
        if json_output:
            print(json.dumps({"imported": 0, "errors": 0, "skipped": skipped, "samples": []}))
        else:
            console.print(f"[green]✔ All {skipped} file(s) already imported — nothing to do.[/green]")
        return

    # ── Lazy-load LocalAIEngine only when --auto-tag is requested ─────────────
    ai_engine = None
    if auto_tag:
        try:
            from samplemind.ai.local_models import LocalAIEngine
            ai_engine = LocalAIEngine()
        except Exception as exc:  # pragma: no cover
            if not json_output:
                console.print(f"[yellow]⚠ Could not load AI engine ({exc}); proceeding without auto-tag.[/yellow]")

    # ── Run analysis (parallel via ProcessPoolExecutor) ──────────────────────
    raw: list[dict]
    use_rich = not json_output and sys.stderr.isatty()

    if not use_rich:
        # CI / JSON mode — no progress bar; stdout must stay clean.
        raw = analyze_batch(wav_files, workers=workers)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
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

            # ── Auto-tag via LocalAIEngine ─────────────────────────────────
            if ai_engine is not None:
                try:
                    tags = ai_engine.generate_tags(r)
                    if tags:
                        SampleRepository.tag(
                            str(path.resolve()),
                            SampleUpdate(tags=",".join(tags)),
                        )
                        r["tags"] = tags
                except Exception:  # pragma: no cover
                    pass  # auto-tag failure is non-fatal

            imported += 1
            results.append(
                {
                    "id": sample.id,
                    "filename": path.name,
                    "path": str(path.resolve()),
                    **{k: r[k] for k in ("bpm", "key", "energy", "mood", "instrument") if k in r},
                    **({"tags": r["tags"]} if "tags" in r else {}),
                }
            )
        except Exception as exc:
            errors += 1
            if not json_output:
                console.print(f"  [red]✗[/red] {path.name} — {exc}")

    # ── Output ────────────────────────────────────────────────────────────────
    if json_output:
        # Rust reads this from stdout; schema must stay stable.
        print(json.dumps({"imported": imported, "errors": errors, "skipped": skipped, "samples": results}))
    else:
        _print_results_table(results)
        parts = [f"[green]✔ Imported {imported} / {len(wav_files)} sample(s)."]
        if skipped:
            parts.append(f"  [dim]{skipped} skipped (duplicate).[/dim]")
        if errors:
            parts.append(f"  [red]{errors} error(s).[/red]")
        parts.append("[/green]")
        console.print("\n" + "".join(parts))


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
