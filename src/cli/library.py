"""
library.py — list and search the sample library.

list:   show everything, with optional BPM/key filters
search: filter by filename, genre, energy, BPM, key simultaneously
"""

from data.database import get_all_samples, search_samples, count_samples, init_db


def _print_table(rows):
    if not rows:
        print("🔍 No samples matched your filters.")
        return
    print(f"\n{'#':<4} {'Filename':<34} {'BPM':<7} {'Key':<10} {'Type':<8} {'Genre':<10} {'Energy':<7} {'Mood'}")
    print("─" * 100)
    for i, r in enumerate(rows, 1):
        print(
            f"{i:<4} {r['filename']:<34} {str(r['bpm']):<7} {(r['key'] or ''):<10} "
            f"{(r['instrument'] or ''):<8} {(r['genre'] or ''):<10} "
            f"{(r['energy'] or ''):<7} {r['mood'] or ''}"
        )
    print()


def list_samples(key=None, bpm_min=None, bpm_max=None):
    init_db()
    total = count_samples()
    if total == 0:
        print("📭 Library is empty. Run `python main.py import <folder>` first.")
        return
    rows = get_all_samples(bpm_min=bpm_min, bpm_max=bpm_max, key=key)
    _print_table(rows)
    print(f"{len(rows)} result(s)  |  {total} total in library")


def search_library(query=None, key=None, bpm_min=None, bpm_max=None,
                   genre=None, energy=None, instrument=None):
    init_db()
    total = count_samples()
    if total == 0:
        print("📭 Library is empty. Run `python main.py import <folder>` first.")
        return
    rows = search_samples(query=query, bpm_min=bpm_min, bpm_max=bpm_max,
                          key=key, genre=genre, energy=energy, instrument=instrument)
    _print_table(rows)
    print(f"{len(rows)} result(s)  |  {total} total in library")
