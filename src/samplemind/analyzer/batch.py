"""
analyzer/batch.py — concurrent batch audio analysis.

Uses ProcessPoolExecutor to parallelize analyze_file() across multiple CPU cores.
Falls back gracefully: if a single file fails, its result contains an 'error' key
instead of raising an exception that would abort the entire batch.

Usage:
    from pathlib import Path
    from samplemind.analyzer.batch import analyze_batch

    paths = list(Path("~/Music").expanduser().rglob("*.wav"))
    results = analyze_batch(paths, workers=4)
    for r in results:
        if "error" in r:
            print(f"Failed: {r['path']} — {r['error']}")
        else:
            print(f"{r['filename']}: {r['bpm']} BPM, {r['instrument']}")
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path

from samplemind.analyzer.audio_analysis import analyze_file


def analyze_batch(
    paths: list[Path],
    workers: int = 0,
    progress_cb: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Analyze multiple audio files in parallel using worker processes.

    Args:
        paths: List of audio file paths to analyze.
        workers: Number of worker processes. 0 means os.cpu_count() (auto).
        progress_cb: Optional callback(completed, total) called after each file
                     finishes. Useful for CLI progress bars.

    Returns:
        List of analysis result dicts in the same order as *paths*.
        Each dict contains the fields returned by analyze_file(), or
        ``{"error": "<msg>", "path": "<path>"}`` if analysis failed.
    """
    if not paths:
        return []

    n_workers = workers or os.cpu_count() or 1
    results: list[dict[str, object]] = [{} for _ in paths]

    # Serial fast-path: avoids spawning worker processes (useful for single files,
    # tests with monkeypatching, and environments where fork is restricted).
    if n_workers == 1:
        for i, p in enumerate(paths):
            try:
                results[i] = dict(analyze_file(str(p)))
            except Exception as exc:
                results[i] = {"error": str(exc), "path": str(p)}
            if progress_cb is not None:
                progress_cb(i + 1, len(paths))
        return results

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        future_to_idx = {pool.submit(analyze_file, str(p)): i for i, p in enumerate(paths)}
        for completed, future in enumerate(as_completed(future_to_idx), start=1):
            idx = future_to_idx[future]
            try:
                results[idx] = dict(future.result())
            except Exception as exc:
                results[idx] = {"error": str(exc), "path": str(paths[idx])}
            if progress_cb is not None:
                progress_cb(completed, len(paths))

    return results

