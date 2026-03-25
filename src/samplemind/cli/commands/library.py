"""List and search the sample library."""

import json
import sys

from samplemind.core.models.sample import Sample
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository


def _sample_to_dict(s: Sample) -> dict:
    """Convert a Sample ORM instance to a plain dict for JSON output."""
    return {
        "id": s.id,
        "filename": s.filename,
        "path": s.path,
        "bpm": s.bpm,
        "key": s.key,
        "mood": s.mood,
        "energy": s.energy,
        "instrument": s.instrument,
        "genre": s.genre,
        "tags": s.tags,
        "imported_at": s.imported_at.isoformat() if s.imported_at else None,
    }


def _print_table(rows: list[Sample]) -> None:
    """Print samples in a formatted table to stderr."""
    if not rows:
        print("🔍 No samples matched your filters.", file=sys.stderr)
        return
    print(
        f"\n{'#':<4} {'Filename':<34} {'BPM':<7} {'Key':<10} "
        f"{'Type':<8} {'Genre':<10} {'Energy':<7} {'Mood'}",
        file=sys.stderr,
    )
    print("─" * 100, file=sys.stderr)
    for i, s in enumerate(rows, 1):
        print(
            f"{i:<4} {s.filename:<34} {str(s.bpm or '?'):<7} {(s.key or ''):<10} "
            f"{(s.instrument or ''):<8} {(s.genre or ''):<10} "
            f"{(s.energy or ''):<7} {s.mood or ''}",
            file=sys.stderr,
        )
    print(file=sys.stderr)


def list_samples(
    key: str | None = None,
    bpm_min: float | None = None,
    bpm_max: float | None = None,
    json_output: bool = False,
) -> None:
    """List all samples in the library with optional filters."""
    init_orm()
    total = SampleRepository.count()
    if total == 0:
        if json_output:
            print(json.dumps({"samples": [], "total": 0}))
        else:
            print(
                "📭 Library is empty. Run `samplemind import <folder>` first.",
                file=sys.stderr,
            )
        return
    rows = SampleRepository.search(bpm_min=bpm_min, bpm_max=bpm_max, key=key)
    if json_output:
        print(json.dumps({"samples": [_sample_to_dict(s) for s in rows], "total": total}))
    else:
        _print_table(rows)
        print(f"{len(rows)} result(s)  |  {total} total in library", file=sys.stderr)


def search_library(
    query: str | None = None,
    key: str | None = None,
    bpm_min: float | None = None,
    bpm_max: float | None = None,
    genre: str | None = None,
    energy: str | None = None,
    instrument: str | None = None,
    json_output: bool = False,
) -> None:
    """Search the library with multiple filters."""
    init_orm()
    total = SampleRepository.count()
    if total == 0:
        if json_output:
            print(json.dumps({"samples": [], "total": 0}))
        else:
            print(
                "📭 Library is empty. Run `samplemind import <folder>` first.",
                file=sys.stderr,
            )
        return
    rows = SampleRepository.search(
        query=query,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        key=key,
        genre=genre,
        energy=energy,
        instrument=instrument,
    )
    if json_output:
        print(json.dumps({"samples": [_sample_to_dict(s) for s in rows], "total": total}))
    else:
        _print_table(rows)
        print(f"{len(rows)} result(s)  |  {total} total in library", file=sys.stderr)
