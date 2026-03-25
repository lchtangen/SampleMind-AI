"""
analyzer/fingerprint.py — SHA-256 fingerprinting for exact duplicate detection

Reading only the first 64 KB is a deliberate speed/accuracy trade-off:
  - Fast enough to fingerprint 1 000 files in under a second
  - Catches exact duplicates and most near-duplicates (same file, different path)
  - Does NOT catch re-encoded versions (different bitrate / format)

Typical use:
    from samplemind.analyzer.fingerprint import find_duplicates
    from pathlib import Path

    dup_groups = find_duplicates(list(Path("/my/samples").glob("**/*.wav")))
    for fp, paths in dup_groups.items():
        print(f"Duplicate group ({fp[:8]}…): {[str(p) for p in paths]}")
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def fingerprint_file(path: Path) -> str:
    """Compute SHA-256 of the first 64 KB of a file.

    Args:
        path: Absolute or relative path to the audio file.

    Returns:
        Lowercase hex digest string (64 characters).

    Raises:
        OSError: If the file cannot be opened or read.
    """
    with open(path, "rb") as f:  # noqa: PTH123
        return hashlib.sha256(f.read(65536)).hexdigest()


def find_duplicates(paths: list[Path]) -> dict[str, list[Path]]:
    """Group paths by SHA-256 fingerprint and return only duplicate groups.

    A group is considered a duplicate only if it contains more than one path,
    i.e. two or more files share the same first-64-KB content.

    Files that cannot be read (missing, permission error) are silently skipped
    rather than crashing the whole scan.

    Args:
        paths: List of file paths to fingerprint. May include non-existent
               paths — they are silently skipped.

    Returns:
        Dict mapping fingerprint → list[Path] for every group with ≥ 2 members.
        Returns an empty dict when no duplicates are found.

    Example:
        >>> groups = find_duplicates(list(Path("/samples").glob("**/*.wav")))
        >>> for fp, dupes in groups.items():
        ...     print(f"  {fp[:8]}…  →  {[p.name for p in dupes]}")
    """
    groups: dict[str, list[Path]] = {}
    for path in paths:
        try:
            fp = fingerprint_file(path)
        except OSError:
            # File may have been deleted between discovery and fingerprinting
            continue
        groups.setdefault(fp, []).append(path)
    return {fp: ps for fp, ps in groups.items() if len(ps) > 1}

