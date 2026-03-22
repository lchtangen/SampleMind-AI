"""
library.py — CLI command to list and search the sample library.

The `list` command queries the SQLite database and prints a table.
Optional filters: --key, --bpm-min, --bpm-max
"""

from data.database import get_all_samples, count_samples, init_db


def list_samples(key=None, bpm_min=None, bpm_max=None):
    init_db()
    total = count_samples()

    if total == 0:
        print("📭 Library is empty. Run `samplemind import <folder>` first.")
        return

    rows = get_all_samples(bpm_min=bpm_min, bpm_max=bpm_max, key=key)

    if not rows:
        print("🔍 No samples matched your filters.")
        return

    # Print a simple table
    print(f"\n{'#':<4} {'Filename':<40} {'BPM':<7} {'Key':<10} {'Imported'}")
    print("─" * 80)
    for i, row in enumerate(rows, 1):
        print(f"{i:<4} {row['filename']:<40} {row['bpm']:<7} {row['key']:<10} {row['imported_at'][:10]}")

    print(f"\n{len(rows)} result(s)  |  {total} total in library")
