"""
cli/commands/export.py — export filtered samples to a target folder

Samples are renamed to an FL Studio-compatible convention:
    {original_stem}_{bpm}bpm_{key}_{energy}.wav

The ``--organize`` option creates subfolders by instrument, mood, or genre so
the exported folder can be dropped directly into an FL Studio browser category.

Usage:
    samplemind export --target ~/Desktop/my-pack
    samplemind export --target ~/export --organize instrument --energy high
    samplemind export --target ~/export --mood dark --bpm-min 120 --bpm-max 140
"""

from __future__ import annotations

from pathlib import Path
import shutil

from rich.console import Console
from rich.table import Table

from samplemind.core.models.sample import Sample
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

_console = Console(stderr=True)
_err = Console(stderr=True, highlight=False)

# Default export folder, relative to current working directory
_DEFAULT_TARGET = Path.cwd() / "samplemind-export"


def _fl_name(sample: Sample) -> str:
    """Build an FL Studio-compatible filename for *sample*.

    Format: ``{stem}_{bpm}bpm_{key}_{energy}.wav``

    Missing metadata is replaced with a safe placeholder so the name is
    always a valid filename on all platforms:
        - bpm  → "nobpm"
        - key  → "nokey"  (spaces replaced with underscore, # with s)
        - energy → "noenergy"

    The key is sanitised to be filesystem-safe:
        "C# maj" → "Cs_maj", "F min" → "F_min"
    """
    stem = Path(sample.filename).stem

    if sample.bpm is not None:
        bpm_str = f"{round(sample.bpm)}bpm"
    else:
        bpm_str = "nobpm"

    if sample.key:
        key_str = sample.key.replace(" ", "_").replace("#", "s")
    else:
        key_str = "nokey"

    energy_str = sample.energy or "noenergy"

    return f"{stem}_{bpm_str}_{key_str}_{energy_str}.wav"


def _subfolder(sample: Sample, organize: str) -> str:
    """Return the subfolder name for a sample given the organize mode."""
    if organize == "instrument":
        return sample.instrument or "unknown"
    if organize == "mood":
        return sample.mood or "unknown"
    if organize == "genre":
        return sample.genre or "untagged"
    return ""  # flat layout when organize is not set


def export_samples(
    target: Path | None = None,
    organize: str | None = None,
    energy: str | None = None,
    instrument: str | None = None,
    mood: str | None = None,
    bpm_min: float | None = None,
    bpm_max: float | None = None,
) -> None:
    """Filter the library and copy matching samples to *target*.

    Args:
        target:     Destination folder. Created if it doesn't exist.
                    Defaults to ``./samplemind-export`` in the current directory.
        organize:   Subfolder grouping: ``"instrument"``, ``"mood"``, or ``"genre"``.
                    Omit (or pass None) for a flat layout.
        energy:     Filter by energy level: ``"low"``, ``"mid"``, or ``"high"``.
        instrument: Filter by instrument label (e.g. ``"kick"``, ``"bass"``).
        mood:       Filter by mood label (e.g. ``"dark"``, ``"euphoric"``).
        bpm_min:    Lower BPM bound (inclusive).
        bpm_max:    Upper BPM bound (inclusive).
    """
    init_orm()

    dest = target or _DEFAULT_TARGET
    dest.mkdir(parents=True, exist_ok=True)

    samples = SampleRepository.search(
        energy=energy,
        instrument=instrument,
        mood=mood,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
    )

    if not samples:
        _err.print("🔍 No samples matched your filters.")
        return

    table = Table(
        title=f"Exporting {len(samples)} sample(s) → {dest}", show_lines=False
    )
    table.add_column("Source", style="dim", no_wrap=True)
    table.add_column("Exported as", style="cyan", no_wrap=True)
    table.add_column("Folder", style="yellow")

    copied = skipped = 0

    for sample in samples:
        src = Path(sample.path)
        if not src.exists():
            _err.print(f"  ⚠️  Missing on disk, skipped: {sample.filename}")
            skipped += 1
            continue

        sub = _subfolder(sample, organize or "")
        out_dir = dest / sub if sub else dest
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / _fl_name(sample)
        shutil.copy2(src, out_path)
        copied += 1

        table.add_row(sample.filename, out_path.name, sub or "(root)")

    _console.print(table)
    _err.print(f"\n✅ Exported {copied} file(s) to [bold]{dest}[/bold]", end="")
    if skipped:
        _err.print(f"  (skipped {skipped} missing file(s))", end="")
    _err.print()
