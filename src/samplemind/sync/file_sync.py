"""Upload and download audio files to/from S3-compatible object storage.

Phase 13 — Cloud Sync.
Uses boto3 with a configurable endpoint_url to support R2, S3, and B2.
push_files() uploads new/changed WAV files, pull_files() downloads files
missing locally. Uses ETag (MD5 hex) comparison to skip unchanged files.

Requires: uv sync --extra sync  (installs boto3)
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from samplemind.sync.config import SyncSettings, get_sync_settings

logger = logging.getLogger(__name__)


def _require_boto3() -> object:
    """Return boto3 module or raise ImportError with install hint."""
    try:
        import boto3  # noqa: PLC0415

        return boto3
    except ImportError as exc:
        raise ImportError(
            "boto3 is required for cloud sync. "
            "Install with: uv sync --extra sync"
        ) from exc


def _md5_hex(path: Path) -> str:
    """Return MD5 hex digest of a file (matches S3 ETag for single-part uploads)."""
    h = hashlib.md5()  # noqa: S324 -- used for ETag comparison only, not security
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_client(settings: SyncSettings) -> object:
    """Create a boto3 S3 client from SyncSettings."""
    boto3 = _require_boto3()
    return boto3.client(  # type: ignore[attr-defined]
        "s3",
        endpoint_url=settings.endpoint_url,
        aws_access_key_id=settings.access_key or None,
        aws_secret_access_key=settings.secret_key or None,
        region_name=settings.region,
    )


def _remote_etag(client: object, bucket: str, key: str) -> str | None:
    """Return the ETag for an object, or None if the object doesn't exist."""
    try:
        resp = client.head_object(Bucket=bucket, Key=key)  # type: ignore[attr-defined]
        return resp["ETag"].strip('"')
    except Exception:
        return None


def push_files(
    paths: list[Path],
    settings: SyncSettings | None = None,
) -> dict[str, int]:
    """Upload new/changed files to S3-compatible storage.

    Files are skipped when the local MD5 matches the remote ETag (unchanged).
    When settings.dry_run is True, no uploads happen.

    Args:
        paths: Local file paths to upload.
        settings: SyncSettings (defaults to environment-loaded config).

    Returns:
        Dict with keys "uploaded", "skipped", "errors".
    """
    cfg = settings or get_sync_settings()
    client = _make_client(cfg)
    uploaded = 0
    skipped = 0
    errors = 0

    for path in paths:
        if not path.exists():
            logger.warning("Skipping missing file: %s", path)
            errors += 1
            continue

        key = cfg.prefix + path.name
        local_md5 = _md5_hex(path)
        remote_etag = _remote_etag(client, cfg.bucket, key)

        if remote_etag == local_md5:
            logger.debug("Skipping unchanged: %s", path.name)
            skipped += 1
            continue

        if cfg.dry_run:
            logger.info("[DRY RUN] Would upload: %s → s3://%s/%s", path, cfg.bucket, key)
            uploaded += 1
            continue

        try:
            client.upload_file(str(path), cfg.bucket, key)  # type: ignore[attr-defined]
            logger.info("Uploaded: %s → s3://%s/%s", path, cfg.bucket, key)
            uploaded += 1
        except Exception as exc:
            logger.error("Upload failed for %s: %s", path, exc)
            errors += 1

    return {"uploaded": uploaded, "skipped": skipped, "errors": errors}


def pull_files(
    dest_dir: Path,
    settings: SyncSettings | None = None,
) -> dict[str, int]:
    """Download files from S3-compatible storage that are missing locally.

    Args:
        dest_dir: Local directory to download files into.
        settings: SyncSettings (defaults to environment-loaded config).

    Returns:
        Dict with keys "downloaded", "skipped", "errors".
    """
    cfg = settings or get_sync_settings()
    client = _make_client(cfg)
    downloaded = 0
    skipped = 0
    errors = 0

    try:
        paginator = client.get_paginator("list_objects_v2")  # type: ignore[attr-defined]
        pages = paginator.paginate(Bucket=cfg.bucket, Prefix=cfg.prefix)

        dest_dir.mkdir(parents=True, exist_ok=True)

        for page in pages:
            for obj in page.get("Contents", []):
                key: str = obj["Key"]
                filename = Path(key).name
                local_path = dest_dir / filename

                if local_path.exists():
                    skipped += 1
                    continue

                if cfg.dry_run:
                    logger.info("[DRY RUN] Would download: s3://%s/%s → %s", cfg.bucket, key, local_path)
                    downloaded += 1
                    continue

                try:
                    client.download_file(cfg.bucket, key, str(local_path))  # type: ignore[attr-defined]
                    logger.info("Downloaded: s3://%s/%s → %s", cfg.bucket, key, local_path)
                    downloaded += 1
                except Exception as exc:
                    logger.error("Download failed for %s: %s", key, exc)
                    errors += 1

    except Exception as exc:
        logger.error("Failed to list objects in s3://%s/%s: %s", cfg.bucket, cfg.prefix, exc)
        errors += 1

    return {"downloaded": downloaded, "skipped": skipped, "errors": errors}
