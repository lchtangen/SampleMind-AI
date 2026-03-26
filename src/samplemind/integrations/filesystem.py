"""Export samples to the FL Studio Patches/Samples/SampleMind folder.

Phase 7 — FL Studio Integration.
Copies filtered WAV files from the SampleMind library into the FL Studio sample
browser directory so they appear immediately in the browser without requiring a
manual rescan.

File naming strategy:
  - If the source path already ends with a well-formed FL-compatible name
    ({stem}_{bpm}bpm_{key}_{energy}.wav), it is preserved.
  - Otherwise, the basename is used as-is to avoid overwriting the user's naming.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from samplemind.integrations.paths import get_fl_studio_paths


def export_to_fl_studio(
    sample_paths: list[Path],
    dest_dir: Path | None = None,
) -> dict[str, int]:
    """Copy sample files into FL Studio's SampleMind directory (or a custom dir).

    Skips a file if the destination copy already exists AND has a modification
    time >= the source (i.e., the copy is up to date).

    Args:
        sample_paths: Absolute paths to WAV files to export.
        dest_dir:     Override destination directory.  If None, auto-detects FL
                      Studio paths via ``get_fl_studio_paths()``.

    Returns:
        Dict with keys:
          "copied"  — number of files successfully copied
          "skipped" — number of files skipped (already up to date)
          "targets" — number of distinct target directories written to

    Raises:
        RuntimeError: If dest_dir is None and no FL Studio installation is found.
    """
    if dest_dir is not None:
        targets = [dest_dir]
    else:
        targets = get_fl_studio_paths()
        if not targets:
            raise RuntimeError(
                "No FL Studio installation detected.  "
                "Install FL Studio or pass dest_dir explicitly."
            )

    copied = 0
    skipped = 0

    for target in targets:
        target.mkdir(parents=True, exist_ok=True)

        for src in sample_paths:
            if not src.exists():
                continue
            dst = target / src.name
            if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                skipped += 1
                continue
            shutil.copy2(src, dst)
            copied += 1

    return {"copied": copied, "skipped": skipped, "targets": len(targets)}


def build_fl_filename(
    stem: str,
    bpm: float | None = None,
    key: str | None = None,
    energy: str | None = None,
) -> str:
    """Build an FL Studio-compatible filename from metadata fields.

    Format: ``{stem}_{bpm}bpm_{key}_{energy}.wav``

    Missing fields are replaced with the placeholder ``"unknown"``.
    ``#`` is replaced with ``s`` (e.g. ``C#`` → ``Cs``) and spaces become ``_``.

    Args:
        stem:   Base filename without extension.
        bpm:    Beats per minute (rounded to nearest integer).
        key:    Musical key string (e.g. ``"C# min"``).
        energy: Energy level (``"low"`` / ``"mid"`` / ``"high"``).

    Returns:
        Sanitised ``.wav`` filename.
    """

    def _safe(value: object) -> str:
        return str(value).replace("#", "s").replace(" ", "_") if value else "unknown"

    bpm_str = f"{round(bpm)}bpm" if bpm is not None else "unknownbpm"
    return f"{stem}_{bpm_str}_{_safe(key)}_{_safe(energy)}.wav"
