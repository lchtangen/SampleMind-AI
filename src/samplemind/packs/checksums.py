"""SHA-256 checksum helpers for .smpack integrity verification.

Uses 64 KB streaming reads so arbitrarily large audio files can be
checksummed without loading them fully into memory.

Used by both:
  - builder.py  (generate checksums when creating a pack)
  - importer.py (verify checksums when importing a pack)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samplemind.packs.models import PackEntry, PackManifest

_CHUNK = 65536  # 64 KB


def checksum_file(path: Path) -> str:
    """Compute the SHA-256 hex digest of an entire file.

    Streams in 64 KB chunks to handle large audio files without
    loading the full content into memory.

    Returns:
        64-character lowercase hex string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_entry(entry: PackEntry, extracted_path: Path) -> bool:
    """Return True iff extracted_path's SHA-256 matches entry.sha256."""
    return checksum_file(extracted_path) == entry.sha256


def verify_manifest_checksums(
    manifest: PackManifest,
    extracted_dir: Path,
) -> list[str]:
    """Verify every entry in a manifest against files in extracted_dir.

    Args:
        manifest:      The PackManifest read from the .smpack archive.
        extracted_dir: Directory into which the archive was extracted.

    Returns:
        List of human-readable failure messages.  Empty list means all
        checksums matched and all files are present.
    """
    failures: list[str] = []
    for entry in manifest.entries:
        fp = extracted_dir / entry.filename
        if not fp.exists():
            failures.append(f"{entry.filename}: missing from archive")
        elif checksum_file(fp) != entry.sha256:
            failures.append(f"{entry.filename}: SHA-256 mismatch")
    return failures
