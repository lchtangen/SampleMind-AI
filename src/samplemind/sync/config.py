"""SyncSettings: provider configuration for cloud sync (R2, S3, B2).

Phase 13 — Cloud Sync.
Pydantic-settings model loaded from environment variables with
SAMPLEMIND_SYNC_ prefix.

Environment variables:
  SAMPLEMIND_SYNC_ENDPOINT_URL   (default: https://s3.amazonaws.com)
  SAMPLEMIND_SYNC_BUCKET         (default: samplemind-library)
  SAMPLEMIND_SYNC_PREFIX         (default: samples/)
  SAMPLEMIND_SYNC_ACCESS_KEY     S3 access key ID
  SAMPLEMIND_SYNC_SECRET_KEY     S3 secret access key
  SAMPLEMIND_SYNC_REGION         (default: auto)
  SAMPLEMIND_SYNC_DRY_RUN        (default: false)
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class SyncSettings(BaseSettings):
    """Configuration for S3-compatible cloud sync.

    Compatible with Cloudflare R2, AWS S3, and Backblaze B2.
    """

    model_config = SettingsConfigDict(env_prefix="SAMPLEMIND_SYNC_")

    endpoint_url: str = "https://s3.amazonaws.com"
    bucket: str = "samplemind-library"
    prefix: str = "samples/"
    access_key: str = ""
    secret_key: str = ""
    region: str = "auto"
    dry_run: bool = False


def get_sync_settings() -> SyncSettings:
    """Return a SyncSettings instance loaded from the environment."""
    return SyncSettings()
