"""
cli/commands/stats.py — Rich summary of library statistics

Prints four Rich tables:
  1. Overview     — total count, samples with/without BPM, analysed vs untagged
  2. By energy    — low / mid / high  (count + %)
  3. By instrument — kick / snare / hihat / bass / pad / lead / loop / sfx / unknown
  4. By mood      — dark / chill / aggressive / euphoric / melancholic / neutral
  Plus a BPM distribution row: min · max · mean · median

Usage:
    samplemind stats
"""

from __future__ import annotations

import statistics
from collections import Counter

from rich.console import Console
from rich.table import Table

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
    table.add_column("Label",   style="cyan",          no_wrap=True)
    table.add_column("Count",   justify="right")
    table.add_column("%",       justify="right", style="dim")

    keys = ordered_keys if ordered_keys else sorted(counter)
    for key in keys:
        count = counter.get(key, 0)
        if count == 0:
            continue
        table.add_row(key, str(count), _pct(count, total))

    # Show "unclassified" (None) as a separate row if present
    none_count = counter.get(None, 0)  # type: ignore[call-overload]
    if none_count:
        table.add_row("[dim]—unclassified—[/dim]", str(none_count), _pct(none_count, total))

    return table


def print_stats() -> None:
    """Fetch all samples and print library statistics using Rich tables."""
    init_orm()

    samples = SampleRepository.get_all()
    total = len(samples)

    if total == 0:
        _err.print("📭 Library is empty. Run `samplemind import <folder>` first.")
        return

    # ── Overview ────────────────────────────────────────────────────────────
    bpms = [s.bpm for s in samples if s.bpm is not None]
    with_bpm    = len(bpms)
    without_bpm = total - with_bpm
    analysed    = sum(1 for s in samples if s.energy is not None)
    tagged      = sum(1 for s in samples if s.genre is not None or s.tags is not None)

    overview = Table(title="Library Overview", show_lines=False, expand=False)
    overview.add_column("Metric", style="bold cyan", no_wrap=True)
    overview.add_column("Value",  justify="right")
    overview.add_row("Total samples",           str(total))
    overview.add_row("With BPM detected",       str(with_bpm))
    overview.add_row("Without BPM",             str(without_bpm))
    overview.add_row("Auto-analysed",            str(analysed))
    overview.add_row("Manually tagged",          str(tagged))

    # ── BPM distribution ────────────────────────────────────────────────────
    if bpms:
        overview.add_section()
        overview.add_row("BPM min",    f"{min(bpms):.1f}")
        overview.add_row("BPM max",    f"{max(bpms):.1f}")
        overview.add_row("BPM mean",   f"{statistics.mean(bpms):.1f}")
        overview.add_row("BPM median", f"{statistics.median(bpms):.1f}")

    _console.print(overview)
    _console.print()

    # ── Energy breakdown ────────────────────────────────────────────────────
    energy_counter: Counter = Counter(s.energy for s in samples)
    _console.print(_breakdown_table(
        "Energy Distribution",
        energy_counter,
        total,
        ordered_keys=["low", "mid", "high"],
    ))
    _console.print()

    # ── Instrument breakdown ────────────────────────────────────────────────
    instrument_counter: Counter = Counter(s.instrument for s in samples)
    _console.print(_breakdown_table(
        "Instrument Distribution",
        instrument_counter,
        total,
        ordered_keys=["kick", "snare", "hihat", "bass", "pad", "lead", "loop", "sfx", "unknown"],
    ))
    _console.print()

    # ── Mood breakdown ───────────────────────────────────────────────────────
    mood_counter: Counter = Counter(s.mood for s in samples)
    _console.print(_breakdown_table(
        "Mood Distribution",
        mood_counter,
        total,
        ordered_keys=["dark", "chill", "aggressive", "euphoric", "melancholic", "neutral"],
    ))

