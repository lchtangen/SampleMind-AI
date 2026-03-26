"""Pack validation and CDN upload for marketplace publishing.

Phase 15 — Marketplace.
validate_pack_for_marketplace() checks .smpack integrity (checksums, manifest
schema, audio file formats). upload_to_cdn() streams the verified archive to
Cloudflare R2 and returns the CDN key for inclusion in the PackListing row.
"""

from __future__ import annotations

from pathlib import Path
import zipfile

from samplemind.packs.models import PackManifest


class PackValidationError(Exception):
    """Raised when a .smpack archive fails marketplace validation."""


def validate_pack_for_marketplace(smpack_path: Path) -> PackManifest:
    """Verify integrity and metadata completeness of a .smpack file.

    Checks performed:

    1. The file is a valid ZIP archive.
    2. ``manifest.json`` is present and parses as a :class:`PackManifest`.
    3. Required manifest fields are non-empty: ``slug``, ``version``, ``entries``.
    4. Every entry in the manifest has a valid path and audio format (WAV/AIFF/MP3).
    5. No entry uses the forbidden energy value ``"medium"`` (use ``"mid"`` instead).
    6. SHA-256 checksums pass for all declared entries.

    Args:
        smpack_path: Path to the ``.smpack`` file on disk.

    Returns:
        The validated :class:`PackManifest`.

    Raises:
        PackValidationError: If any check fails.
        FileNotFoundError: If *smpack_path* does not exist.
    """
    from samplemind.packs.checksums import verify_manifest_checksums

    if not smpack_path.exists():
        raise FileNotFoundError(smpack_path)

    if not zipfile.is_zipfile(smpack_path):
        raise PackValidationError(f"{smpack_path.name} is not a valid ZIP archive.")

    with zipfile.ZipFile(smpack_path) as zf:
        names = zf.namelist()
        if "manifest.json" not in names:
            raise PackValidationError("manifest.json not found in archive.")

        manifest_bytes = zf.read("manifest.json")

    try:
        manifest = PackManifest.model_validate_json(manifest_bytes)
    except Exception as exc:
        raise PackValidationError(f"manifest.json parse error: {exc}") from exc

    # Required fields
    if not manifest.slug:
        raise PackValidationError("manifest.slug is empty.")
    if not manifest.version:
        raise PackValidationError("manifest.version is empty.")
    if not manifest.entries:
        raise PackValidationError("manifest.entries is empty — pack has no samples.")

    # Check for disallowed energy value and audio formats
    allowed_formats = {".wav", ".aiff", ".aif", ".mp3"}
    for entry in manifest.entries:
        if getattr(entry, "energy", None) == "medium":
            raise PackValidationError(
                f"Entry {entry.filename!r} uses energy='medium'. "
                "Use 'low', 'mid', or 'high' instead."
            )
        suffix = Path(entry.filename).suffix.lower()
        if suffix not in allowed_formats:
            raise PackValidationError(
                f"Entry {entry.filename!r} has unsupported format {suffix!r}. "
                f"Allowed: {sorted(allowed_formats)}"
            )

    # Verify checksums
    try:
        verify_manifest_checksums(smpack_path, manifest)
    except Exception as exc:
        raise PackValidationError(f"Checksum verification failed: {exc}") from exc

    return manifest


def upload_to_cdn(
    smpack_path: Path,
    settings: object | None = None,
) -> str:
    """Stream *smpack_path* to Cloudflare R2 and return the CDN object key.

    The object key is ``packs/<filename>`` — e.g.
    ``packs/dark-trap-essentials-v2.smpack``.

    Args:
        smpack_path: Local ``.smpack`` file to upload.
        settings: :class:`~samplemind.sync.config.SyncSettings` instance.
            Defaults to ``get_sync_settings()``.

    Returns:
        The R2 object key string (``packs/<filename>``).

    Raises:
        FileNotFoundError: If *smpack_path* does not exist.
        ImportError: If boto3 is not installed.
    """
    from samplemind.sync.config import get_sync_settings
    from samplemind.sync.file_sync import _make_client  # type: ignore[attr-defined]

    if not smpack_path.exists():
        raise FileNotFoundError(smpack_path)

    resolved_settings = settings or get_sync_settings()
    client = _make_client(resolved_settings)

    key = f"packs/{smpack_path.name}"
    client.upload_file(
        str(smpack_path),
        resolved_settings.bucket,
        key,
        ExtraArgs={"ContentType": "application/zip"},
    )
    return key
