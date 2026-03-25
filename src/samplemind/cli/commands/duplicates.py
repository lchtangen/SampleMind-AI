"""
cli/commands/duplicates.py — detect and optionally remove exact duplicate WAV files

Duplicate detection uses SHA-256 of the first 64 KB of each file — fast enough
for large libraries and reliable for exact-copy detection.

Usage:
    samplemind duplicates                   # list duplicate groups
    samplemind duplicates --remove          # delete all but the earliest import
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys

from rich.console import Console
from rich.table import Table

from samplemind.analyzer.fingerprint import find_duplicates
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

_console = Console(stderr=True)
_err = Console(stderr=True, highlight=False)


def _fmt_size(path: Path) -> str:
    """Return a human-readable file size string, e.g. '3.2 MB'."""
    try:
        size = path.stat().st_size
    except OSError:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024  # type: ignore[assignment]
    return f"{size:.1f} TB"


def find_library_duplicates(*, remove: bool = False) -> None:
    """Scan the library for exact duplicate WAV files using SHA-256 fingerprinting.

    Args:
        remove: When True, delete all but the earliest-imported copy of each
                duplicate group from both the filesystem and the database.
    """
    init_orm()

    all_samples = SampleRepository.get_all()
    if not all_samples:
        _err.print("📭 Library is empty. Run `samplemind import <folder>` first.")
        return

    # Only fingerprint files that still exist on disk
    on_disk = [s for s in all_samples if Path(s.path).exists()]
    if not on_disk:
        _err.print("⚠️  No library files found on disk.")
        return

    _err.print(f"🔍 Scanning {len(on_disk)} files for duplicates…")
    dup_groups = find_duplicates([Path(s.path) for s in on_disk])

    if not dup_groups:
        _err.print("✅ No duplicate files found.")
        return

    # Build a lookup so we can find Sample metadata for each path
    path_to_sample = {s.path: s for s in on_disk}

    table = Table(
        title=f"Duplicate Groups ({len(dup_groups)} found)",
        show_lines=True,
    )
    table.add_column("Role", style="bold", no_wrap=True)
    table.add_column("Filename", style="cyan", no_wrap=True)
    table.add_column("Size", justify="right")
    table.add_column("Imported", style="dim")
    table.add_column("Path", style="dim")

    total_removed = 0
    total_freed = 0

    for dup_paths in dup_groups.values():
        # Sort by imported_at ascending — keep the earliest import (index 0)
        _epoch = datetime.min.replace(tzinfo=UTC)  # fallback for null imported_at
        dup_samples = sorted(
            [path_to_sample[str(p)] for p in dup_paths if str(p) in path_to_sample],
            key=lambda s: s.imported_at or _epoch,
        )

        for i, sample in enumerate(dup_samples):
            p = Path(sample.path)
            role = "[green]KEEP[/green]" if i == 0 else "[red]DUPE[/red]"
            imported = (
                sample.imported_at.strftime("%Y-%m-%d %H:%M")
                if sample.imported_at
                else "?"
            )
            table.add_row(role, sample.filename, _fmt_size(p), imported, sample.path)

            if remove and i > 0:
                size_bytes = p.stat().st_size if p.exists() else 0
                p.unlink(missing_ok=True)
                SampleRepository.delete_by_path(sample.path)
                total_removed += 1
                total_freed += size_bytes

        table.add_section()  # visual separator between groups

    _console.print(table)

    if remove:
        freed_mb = total_freed / (1024 * 1024)
        _err.print(
            f"\n🗑️  Removed {total_removed} duplicate(s), freed {freed_mb:.1f} MB."
        )
    else:
        dupe_count = sum(len(ps) - 1 for ps in dup_groups.values())
        _err.print(
            f"\n💡 {dupe_count} duplicate file(s) found. "
            "Run with [bold]--remove[/bold] to delete them."
        )
        sys.exit(1)  # non-zero exit signals duplicates exist (useful in CI)
