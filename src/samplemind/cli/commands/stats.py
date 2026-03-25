"""
cli/commands/stats.py — Rich summary of library statistics

Prints four Rich tables:
  1. Overview     — total count, samples with/without BPM, analysed vs untagged
  2. By energy    — low / mid / high  (count + %)
  3. By instrument — kick / snare / hihat / bass / pad / lead / loop / sfx / unknown
  4. By mood      — dark / chill / aggressive / euphoric / melancholic / neutral
  Plus a BPM distribution row: min · max · mean · median

Usage:
    samplemind stats           # human-readable Rich tables (to stdout)
    samplemind stats --json    # machine-readable JSON (to stdout for Tauri/sidecar)

IPC contract (--json mode):
    stdout: JSON object — schema:
      {
        "total": int,
        "with_bpm": int,
        "without_bpm": int,
        "analysed": int,
        "tagged": int,
        "bpm": {"min": float, "max": float, "mean": float, "median": float} | null,
        "by_energy": {"low": int, "mid": int, "high": int, ...},
        "by_instrument": {"kick": int, "snare": int, ...},
        "by_mood": {"dark": int, "chill": int, ...}
      }
"""

from __future__ import annotations

from collections import Counter
import json
import statistics
import sys
from typing import Any

from rich.console import Console
from rich.table import Table
import typer

from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

_console = Console()
_err = Console(stderr=True, highlight=False)


def _pct(count: int, total: int) -> str:
    """Format count as a percentage string, e.g. '42.3 %'."""
    if total == 0:
        return "—"
    return f"{100 * count / total:.1f} %"


def _breakdown_table(
    title: str,
    counter: Counter,
    total: int,
    ordered_keys: list[str] | None = None,
) -> Table:
    """Build a Rich table showing count and percentage for each category."""
    table = Table(title=title, show_lines=False, expand=False)
    table.add_column("Label", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right")
    table.add_column("%", justify="right", style="dim")

    keys = ordered_keys if ordered_keys else sorted(counter)
    for key in keys:
        count = counter.get(key, 0)
        if count == 0:
            continue
        table.add_row(key, str(count), _pct(count, total))

    # Show "unclassified" (None) as a separate row if present
    none_count = counter.get(None, 0)  # type: ignore[call-overload]
    if none_count:
        table.add_row(
            "[dim]—unclassified—[/dim]", str(none_count), _pct(none_count, total)
        )

    return table


def _compute_stats(samples: list) -> dict[str, Any]:
    """Extract library statistics from a list of Sample objects.

    Pure data function — no Rich output, safe to call from tests and JSON mode.

    Returns a dict matching the IPC JSON schema documented in the module docstring.
    """
    total = len(samples)
    bpms = [s.bpm for s in samples if s.bpm is not None]

    bpm_stats: dict[str, float] | None = None
    if bpms:
        bpm_stats = {
            "min": round(min(bpms), 2),
            "max": round(max(bpms), 2),
            "mean": round(statistics.mean(bpms), 2),
            "median": round(statistics.median(bpms), 2),
        }

    energy_counter: Counter = Counter(s.energy for s in samples)
    instrument_counter: Counter = Counter(s.instrument for s in samples)
    mood_counter: Counter = Counter(s.mood for s in samples)

    return {
        "total": total,
        "with_bpm": len(bpms),
        "without_bpm": total - len(bpms),
        "analysed": sum(1 for s in samples if s.energy is not None),
        "tagged": sum(1 for s in samples if s.genre is not None or s.tags is not None),
        "bpm": bpm_stats,
        "by_energy": {k: v for k, v in energy_counter.items() if k is not None},
        "by_instrument": {k: v for k, v in instrument_counter.items() if k is not None},
        "by_mood": {k: v for k, v in mood_counter.items() if k is not None},
    }


def print_stats(
    json_output: bool = typer.Option(
        False, "--json", help="Output stats as JSON to stdout (machine-readable)."
    ),
) -> None:
    """Fetch all samples and print library statistics using Rich tables."""
    init_orm()

    samples = SampleRepository.get_all()

    if json_output:
        stats = _compute_stats(samples)
        print(json.dumps(stats), file=sys.stdout)
        return

    total = len(samples)

    if total == 0:
        _err.print("📭 Library is empty. Run `samplemind import <folder>` first.")
        return

    stats = _compute_stats(samples)
    bpms = [s.bpm for s in samples if s.bpm is not None]

    # ── Overview ────────────────────────────────────────────────────────────
    overview = Table(title="Library Overview", show_lines=False, expand=False)
    overview.add_column("Metric", style="bold cyan", no_wrap=True)
    overview.add_column("Value", justify="right")
    overview.add_row("Total samples", str(stats["total"]))
    overview.add_row("With BPM detected", str(stats["with_bpm"]))
    overview.add_row("Without BPM", str(stats["without_bpm"]))
    overview.add_row("Auto-analysed", str(stats["analysed"]))
    overview.add_row("Manually tagged", str(stats["tagged"]))

    # ── BPM distribution ────────────────────────────────────────────────────
    if bpms and stats["bpm"]:
        bpm = stats["bpm"]
        overview.add_section()
        overview.add_row("BPM min", f"{bpm['min']:.1f}")
        overview.add_row("BPM max", f"{bpm['max']:.1f}")
        overview.add_row("BPM mean", f"{bpm['mean']:.1f}")
        overview.add_row("BPM median", f"{bpm['median']:.1f}")

    _console.print(overview)
    _console.print()

    # ── Energy breakdown ────────────────────────────────────────────────────
    energy_counter: Counter = Counter(s.energy for s in samples)
    _console.print(
        _breakdown_table(
            "Energy Distribution",
            energy_counter,
            total,
            ordered_keys=["low", "mid", "high"],
        )
    )
    _console.print()

    # ── Instrument breakdown ────────────────────────────────────────────────
    instrument_counter: Counter = Counter(s.instrument for s in samples)
    _console.print(
        _breakdown_table(
            "Instrument Distribution",
            instrument_counter,
            total,
            ordered_keys=[
                "kick",
                "snare",
                "hihat",
                "bass",
                "pad",
                "lead",
                "loop",
                "sfx",
                "unknown",
            ],
        )
    )
    _console.print()

    # ── Mood breakdown ───────────────────────────────────────────────────────
    mood_counter: Counter = Counter(s.mood for s in samples)
    _console.print(
        _breakdown_table(
            "Mood Distribution",
            mood_counter,
            total,
            ordered_keys=[
                "dark",
                "chill",
                "aggressive",
                "euphoric",
                "melancholic",
                "neutral",
            ],
        )
    )
