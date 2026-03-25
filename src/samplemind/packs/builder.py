"""Build .smpack ZIP archives from a directory of WAV files.

A .smpack file is a standard ZIP archive with:
  manifest.json   -- PackManifest JSON at the archive root
  <filename>.wav  -- audio files preserving their relative paths

SHA-256 checksums are computed from the original files and embedded in
the manifest so that importers can verify integrity byte-for-byte.
"""

from __future__ import annotations

import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from samplemind.packs.checksums import checksum_file
from samplemind.packs.models import PackEntry, PackManifest


class PackBuildError(Exception):
    """Raised when a .smpack archive cannot be built (e.g. no WAV files)."""


def create_pack(
    wav_dir: Path,
    name: str,
    version: str,
    author: str,
    description: str,
    output_path: Path | None = None,
    metadata_overrides: dict[str, dict] | None = None,
) -> Path:
    """Build a .smpack ZIP archive from a directory of WAV files.

    The archive contains manifest.json (with per-file SHA-256 checksums)
    and all WAV files preserving their directory structure relative to
    wav_dir.

    Args:
        wav_dir:             Root directory scanned recursively for *.wav files.
        name:                Pack name (human-readable, used in manifest).
        version:             Semver string, e.g. '1.0.0'.
        author:              Creator name or handle.
        description:         Short description for the pack browser.
        output_path:         Destination .smpack path.  Auto-generated from
                             name + version if None.
        metadata_overrides:  Mapping of filename (basename or rel-path) to a
                             dict of SampleMind metadata fields to embed in
                             each PackEntry, e.g.::

                               {"kick_128.wav": {"bpm": 128.0, "energy": "high"}}

    Returns:
        Absolute path to the created .smpack file.

    Raises:
        PackBuildError: If no WAV files are found under wav_dir.
        ValidationError: If version/energy values are invalid.
    """
    wav_files = sorted(wav_dir.rglob("*.wav"))
    if not wav_files:
        raise PackBuildError(f"No WAV files found under: {wav_dir}")

    overrides = metadata_overrides or {}
    _entry_fields = set(PackEntry.model_fields)

    entries: list[PackEntry] = []
    for wav in wav_files:
        rel = wav.relative_to(wav_dir).as_posix()
        # Allow overrides keyed by basename OR by relative path
        meta = overrides.get(wav.name, overrides.get(rel, {}))
        entries.append(
            PackEntry(
                filename=rel,
                sha256=checksum_file(wav),
                size_bytes=wav.stat().st_size,
                **{k: v for k, v in meta.items() if k in _entry_fields},
            )
        )

    manifest = PackManifest(
        name=name,
        version=version,
        author=author,
        description=description,
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        entries=entries,
    )

    if output_path is None:
        safe_name = re.sub(r"[^\w.-]", "_", name.lower()).strip("_")
        output_path = wav_dir.parent / f"{safe_name}_{version}.smpack"

    with zipfile.ZipFile(
        output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as zf:
        zf.writestr("manifest.json", manifest.model_dump_json(indent=2))
        for wav in wav_files:
            zf.write(wav, wav.relative_to(wav_dir).as_posix())

    return output_path.resolve()
