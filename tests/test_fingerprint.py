"""
tests/test_fingerprint.py — Tests for SHA-256 audio fingerprinting and duplicate detection.

Tests cover:
  - fingerprint_file(): consistent SHA-256 hash of first 64 KB
  - find_duplicates():  groups identical files, ignores unique files
  - Edge cases:         different content → different hash, empty groups excluded
"""

from pathlib import Path

from samplemind.analyzer.fingerprint import find_duplicates, fingerprint_file


def test_fingerprint_is_consistent(silent_wav: Path) -> None:
    """Same file fingerprinted twice must return identical hash."""
    h1 = fingerprint_file(silent_wav)
    h2 = fingerprint_file(silent_wav)
    assert h1 == h2


def test_fingerprint_is_sha256_format(silent_wav: Path) -> None:
    """Fingerprint must be a 64-character lowercase hex string (SHA-256)."""
    h = fingerprint_file(silent_wav)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_different_files_have_different_fingerprints(
    silent_wav: Path, kick_wav: Path
) -> None:
    """Files with different audio content must have different fingerprints."""
    h_silent = fingerprint_file(silent_wav)
    h_kick = fingerprint_file(kick_wav)
    assert h_silent != h_kick


def test_find_duplicates_detects_copies(tmp_path: Path, silent_wav: Path) -> None:
    """Two files with identical content must be grouped as duplicates."""
    copy = tmp_path / "copy.wav"
    copy.write_bytes(silent_wav.read_bytes())

    dupes = find_duplicates([silent_wav, copy])
    assert len(dupes) == 1  # one duplicate group
    group = next(iter(dupes.values()))
    assert len(group) == 2  # both files in the group


def test_find_duplicates_ignores_unique_files(
    silent_wav: Path, kick_wav: Path
) -> None:
    """Unique files must not appear in the duplicate groups dict."""
    dupes = find_duplicates([silent_wav, kick_wav])
    assert len(dupes) == 0  # no duplicates


def test_find_duplicates_empty_list() -> None:
    """Empty input must return empty dict without raising."""
    dupes = find_duplicates([])
    assert dupes == {}
