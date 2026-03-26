"""Signed Cloudflare R2 download URL generation for purchased packs.

Phase 15 — Marketplace.
generate_signed_url() returns a time-limited presigned URL for a pack's R2
object key (valid 1 hour by default). Uses boto3 presigned URLs against the
R2 S3-compatible endpoint. Called after Stripe payment confirmation.
"""

from __future__ import annotations


def generate_signed_url(
    r2_key: str,
    ttl_seconds: int = 3600,
    settings: object | None = None,
) -> str:
    """Return a time-limited presigned GET URL for *r2_key*.

    The URL grants the holder read access to the R2 object for *ttl_seconds*
    (default 1 hour) without requiring AWS credentials on the client side.

    Args:
        r2_key: Object key in the R2 bucket, e.g. ``packs/dark-trap-v2.smpack``.
        ttl_seconds: URL validity window in seconds.  Maximum enforced by R2
            is 7 days (604800 s).
        settings: :class:`~samplemind.sync.config.SyncSettings` instance.
            Defaults to ``get_sync_settings()``.

    Returns:
        A presigned HTTPS URL string.

    Raises:
        ImportError: If boto3 is not installed.
    """
    from samplemind.sync.config import get_sync_settings
    from samplemind.sync.file_sync import _make_client  # type: ignore[attr-defined]

    resolved_settings = settings or get_sync_settings()
    client = _make_client(resolved_settings)

    url: str = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": resolved_settings.bucket, "Key": r2_key},
        ExpiresIn=ttl_seconds,
    )
    return url
