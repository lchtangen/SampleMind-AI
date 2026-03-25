# Phase 13 — Cloud Sync & Multi-Device

> **Goal:** Sync the SampleMind library across multiple machines — studio Mac,
> home Mac, Windows laptop — with conflict resolution and team collaboration.
>
> **Stack:** Cloudflare R2 (or AWS S3) for file storage · Supabase for metadata sync ·
> Python-boto3 for S3 API · Tauri's built-in HTTP for upload progress ·
> CRDTs for conflict-free metadata merging.
>
> **Prerequisites:** Phase 3 (database schema), Phase 10 (auth system).

---

## 1. Architecture

```
Machine A (Studio Mac)          Machine B (Home Mac)         Machine C (Windows)
┌────────────────────┐          ┌────────────────────┐       ┌────────────────────┐
│ SampleMind library │          │ SampleMind library │       │ SampleMind library │
│ ~/.samplemind/     │          │ ~/.samplemind/     │       │ %APPDATA%/...      │
│ library.db         │          │ library.db         │       │ library.db         │
└────────────────────┘          └────────────────────┘       └────────────────────┘
          │                               │                            │
          └───────────────────────────────┴────────────────────────────┘
                                          │
                                          ▼
                              ┌─────────────────────┐
                              │   Sync Service       │
                              │                      │
                              │  Metadata: Supabase  │← SQLite CDC
                              │  Files: Cloudflare R2│← SHA-256 dedup
                              │  Conflicts: CRDT     │
                              └─────────────────────┘
```

**Design decisions:**
- **Metadata sync (Supabase):** PostgreSQL-backed, real-time, free tier sufficient
- **File sync (R2/S3):** Only files not already in the cloud (SHA-256 dedup)
- **Conflict strategy:** Last-write-wins for metadata; files are immutable (SHA-256 ID)
- **Offline first:** All operations work without cloud; sync is additive

---

## 2. Sync Configuration

```python
# src/samplemind/sync/config.py
"""
Cloud sync configuration.

Set via environment variables or ~/.samplemind/config.toml:
  SAMPLEMIND_SYNC_ENABLED=true
  SAMPLEMIND_SYNC_PROVIDER=cloudflare_r2  # or aws_s3 | backblaze_b2
  SAMPLEMIND_SYNC_BUCKET=samplemind-user-abc123
  SAMPLEMIND_SYNC_ACCESS_KEY=...
  SAMPLEMIND_SYNC_SECRET_KEY=...
  SAMPLEMIND_SYNC_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
  SAMPLEMIND_SUPABASE_URL=https://<project>.supabase.co
  SAMPLEMIND_SUPABASE_KEY=...
"""
from __future__ import annotations
from pydantic import Field
from pydantic_settings import BaseSettings


class SyncSettings(BaseSettings):
    sync_enabled: bool = False
    sync_provider: str = "cloudflare_r2"   # cloudflare_r2 | aws_s3 | backblaze_b2
    sync_bucket: str = ""
    sync_access_key: str = ""
    sync_secret_key: str = ""
    sync_endpoint_url: str = ""            # empty = AWS default endpoint
    sync_prefix: str = ""                  # S3 key prefix (e.g. "user_abc123/")
    supabase_url: str = ""
    supabase_key: str = ""
    device_id: str = Field(
        default_factory=lambda: __import__("uuid").str(uuid.getnode()),
        description="Unique device identifier for conflict resolution"
    )

    class Config:
        env_prefix = "SAMPLEMIND_"
        env_file = ".env"
```

---

## 3. File Sync — Cloudflare R2 / S3

```python
# src/samplemind/sync/file_sync.py
"""
File sync to Cloudflare R2 / AWS S3 / Backblaze B2.

All three providers implement the S3 API — only the endpoint_url differs.

Strategy:
  - Upload: only if SHA-256 not already in bucket (checked via HeadObject)
  - Download: only if SHA-256 not in local library
  - Delete: NEVER auto-delete remote files (user must do it manually)
  - Progress: yields (uploaded_bytes, total_bytes) tuples for UI

File key format in S3:
  {prefix}/audio/{sha256[:2]}/{sha256}.wav

This distributes files across 256 "folders" to avoid S3 prefix throttling.
"""
from __future__ import annotations
import boto3
import hashlib
from pathlib import Path
from typing import Generator
from samplemind.sync.config import SyncSettings
from samplemind.core.logging import get_logger

log = get_logger(__name__)


def get_s3_client(settings: SyncSettings):
    kwargs = {
        "aws_access_key_id":     settings.sync_access_key,
        "aws_secret_access_key": settings.sync_secret_key,
        "region_name":           "auto",  # Cloudflare R2 uses "auto"
    }
    if settings.sync_endpoint_url:
        kwargs["endpoint_url"] = settings.sync_endpoint_url
    return boto3.client("s3", **kwargs)


def upload_file(
    path: Path,
    sha256: str,
    settings: SyncSettings,
) -> str:
    """
    Upload a WAV file to S3/R2 if not already present.

    Returns:
        S3 key of the uploaded file (or existing file if already present)
    """
    s3 = get_s3_client(settings)
    key = f"{settings.sync_prefix}audio/{sha256[:2]}/{sha256}{path.suffix}"

    # Skip upload if already in bucket (idempotent)
    try:
        s3.head_object(Bucket=settings.sync_bucket, Key=key)
        log.debug("file_already_synced", sha256=sha256[:8])
        return key
    except s3.exceptions.ClientError:
        pass  # Not found — proceed with upload

    file_size = path.stat().st_size
    s3.upload_file(
        str(path),
        settings.sync_bucket,
        key,
        ExtraArgs={"ContentType": "audio/wav",
                   "Metadata": {"sha256": sha256, "original_name": path.name}},
        Callback=lambda bytes_sent: log.debug("upload_progress",
                                               sha256=sha256[:8],
                                               pct=round(bytes_sent / file_size * 100)),
    )
    log.info("file_uploaded", key=key, size_mb=round(file_size / 1e6, 2))
    return key


def sync_library_files(settings: SyncSettings) -> dict:
    """
    Upload all library files not yet in cloud storage.

    Returns:
        {"uploaded": N, "skipped": N, "errors": N, "bytes_uploaded": M}
    """
    from samplemind.data.repositories.sample_repository import SampleRepository
    samples = SampleRepository.get_all()
    stats = {"uploaded": 0, "skipped": 0, "errors": 0, "bytes_uploaded": 0}

    for sample in samples:
        try:
            path = Path(sample.path)
            if not path.exists():
                stats["errors"] += 1
                continue
            sha256 = sample.sha256 or hashlib.sha256(path.read_bytes()[:65536]).hexdigest()
            upload_file(path, sha256, settings)
            stats["uploaded"] += 1
            stats["bytes_uploaded"] += path.stat().st_size
        except Exception as e:
            log.error("upload_failed", path=sample.path, error=str(e))
            stats["errors"] += 1

    return stats
```

---

## 4. Metadata Sync — Supabase Realtime

```python
# src/samplemind/sync/metadata_sync.py
"""
Metadata sync via Supabase (PostgreSQL + Realtime WebSocket).

Supabase table schema (create via Supabase dashboard or SQL editor):

  CREATE TABLE synced_samples (
      device_id    TEXT,
      sample_id    INTEGER,
      sha256       TEXT UNIQUE,
      filename     TEXT,
      path         TEXT,
      bpm          REAL,
      key          TEXT,
      instrument   TEXT,
      energy       TEXT,
      mood         TEXT,
      tags         TEXT,
      lufs         REAL,
      updated_at   TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (device_id, sha256)
  );

  CREATE INDEX ON synced_samples(sha256);

Conflict resolution: last-write-wins by updated_at.
The sha256 column ensures the same audio file is never duplicated,
even if it has different paths on different machines.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from samplemind.sync.config import SyncSettings
from samplemind.data.orm import get_db_path
from samplemind.core.logging import get_logger

log = get_logger(__name__)


def push_metadata(settings: SyncSettings) -> dict:
    """Push all local metadata changes to Supabase."""
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("Install supabase: uv add supabase")

    client = create_client(settings.supabase_url, settings.supabase_key)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    samples = conn.execute("""
        SELECT id, sha256, filename, path, bpm, key, instrument,
               energy, mood, tags, lufs_integrated
        FROM samples
        WHERE sha256 IS NOT NULL
    """).fetchall()
    conn.close()

    records = []
    for s in samples:
        d = dict(s)
        records.append({
            "device_id":   settings.device_id,
            "sample_id":   d.pop("id"),
            "sha256":      d["sha256"],
            "filename":    d["filename"],
            "path":        d["path"],
            "bpm":         d["bpm"],
            "key":         d["key"],
            "instrument":  d["instrument"],
            "energy":      d["energy"],
            "mood":        d["mood"],
            "tags":        d.get("tags", ""),
            "lufs":        d.get("lufs_integrated"),
            "updated_at":  datetime.now(timezone.utc).isoformat(),
        })

    # Upsert in batches of 500
    batch_size = 500
    pushed = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("synced_samples").upsert(batch).execute()
        pushed += len(batch)

    log.info("metadata_pushed", count=pushed, device=settings.device_id[:8])
    return {"pushed": pushed}


def pull_metadata(settings: SyncSettings) -> dict:
    """Pull metadata from other devices and merge into local DB."""
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("Install supabase: uv add supabase")

    client = create_client(settings.supabase_url, settings.supabase_key)

    # Fetch all records NOT from this device
    response = (
        client.table("synced_samples")
        .select("*")
        .neq("device_id", settings.device_id)
        .execute()
    )
    remote_samples = response.data

    conn = sqlite3.connect(get_db_path())
    merged = 0
    for remote in remote_samples:
        # Only merge if SHA-256 not already in local DB
        existing = conn.execute(
            "SELECT id FROM samples WHERE sha256 = ?", (remote["sha256"],)
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT OR IGNORE INTO samples
                  (sha256, filename, path, bpm, key, instrument, energy, mood, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (remote["sha256"], remote["filename"], remote["path"],
                  remote["bpm"], remote["key"], remote["instrument"],
                  remote["energy"], remote["mood"], remote.get("tags", "")))
            merged += 1

    conn.commit()
    conn.close()
    log.info("metadata_pulled", merged=merged)
    return {"merged": merged, "total_remote": len(remote_samples)}
```

---

## 5. Sync CLI Commands

```python
# src/samplemind/cli/commands/sync_cmd.py
"""
Cloud sync commands.

Usage:
  uv run samplemind sync push        # push metadata + new files
  uv run samplemind sync pull        # pull metadata from other devices
  uv run samplemind sync status      # show sync status
  uv run samplemind sync config      # show sync configuration
"""
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Cloud sync — multi-device library sync")
console = Console(stderr=True)


@app.command()
def push(files: bool = typer.Option(True, "--files/--no-files", help="Also sync audio files"),
         json_output: bool = typer.Option(False, "--json")):
    """Push local library metadata (and files) to cloud."""
    from samplemind.sync.config import SyncSettings
    from samplemind.sync.metadata_sync import push_metadata
    settings = SyncSettings()
    if not settings.sync_enabled:
        console.print("[yellow]Cloud sync not configured.[/yellow]")
        console.print("Set SAMPLEMIND_SYNC_ENABLED=true and configure credentials.")
        raise typer.Exit(1)

    result = push_metadata(settings)
    if files:
        from samplemind.sync.file_sync import sync_library_files
        file_result = sync_library_files(settings)
        result.update(file_result)

    console.print(f"[green]Pushed:[/green] {result.get('pushed', 0)} metadata records, "
                  f"{result.get('uploaded', 0)} files")


@app.command()
def pull(json_output: bool = typer.Option(False, "--json")):
    """Pull metadata from other devices into local library."""
    from samplemind.sync.config import SyncSettings
    from samplemind.sync.metadata_sync import pull_metadata
    settings = SyncSettings()
    if not settings.sync_enabled:
        console.print("[yellow]Cloud sync not configured.[/yellow]")
        raise typer.Exit(1)
    result = pull_metadata(settings)
    console.print(f"[green]Merged:[/green] {result['merged']} new samples from other devices")


@app.command()
def status():
    """Show sync configuration and last sync times."""
    from samplemind.sync.config import SyncSettings
    settings = SyncSettings()
    table = Table(title="Sync Status")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("Enabled",    str(settings.sync_enabled))
    table.add_row("Provider",   settings.sync_provider)
    table.add_row("Bucket",     settings.sync_bucket or "(not set)")
    table.add_row("Device ID",  settings.device_id[:16] + "...")
    table.add_row("Supabase",   settings.supabase_url[:30] + "..." if settings.supabase_url else "(not set)")
    console.print(table)
```

---

## 6. Testing

```python
# tests/test_cloud_sync.py
"""
Tests for Phase 13 cloud sync.
All S3 and Supabase calls are mocked — no cloud credentials needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@patch("boto3.client")
def test_upload_file_skips_existing(mock_boto, tmp_path, silent_wav):
    """Should skip upload if file already exists in S3 (HeadObject succeeds)."""
    from samplemind.sync.file_sync import upload_file
    from samplemind.sync.config import SyncSettings

    settings = SyncSettings(
        sync_enabled=True, sync_bucket="test-bucket",
        sync_access_key="key", sync_secret_key="secret",
    )
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    # HeadObject succeeds → file already exists
    mock_s3.head_object.return_value = {}

    key = upload_file(silent_wav, "abc123def456", settings)
    mock_s3.upload_file.assert_not_called()   # should NOT upload again
    assert "abc123" in key


@patch("boto3.client")
def test_upload_file_uploads_when_missing(mock_boto, silent_wav):
    """Should upload when HeadObject raises ClientError (file not in bucket)."""
    from samplemind.sync.file_sync import upload_file
    from samplemind.sync.config import SyncSettings
    import botocore.exceptions

    settings = SyncSettings(
        sync_enabled=True, sync_bucket="test-bucket",
        sync_access_key="key", sync_secret_key="secret",
    )
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    # HeadObject raises → file not found → upload needed
    mock_s3.exceptions.ClientError = botocore.exceptions.ClientError
    mock_s3.head_object.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "404"}}, "HeadObject"
    )

    upload_file(silent_wav, "abc123def456", settings)
    mock_s3.upload_file.assert_called_once()


def test_sync_settings_default_device_id():
    """Device ID should be non-empty and consistent across calls."""
    from samplemind.sync.config import SyncSettings
    s1 = SyncSettings()
    s2 = SyncSettings()
    assert s1.device_id == s2.device_id
    assert len(s1.device_id) > 0
```

---

## 7. Checklist

- [ ] `uv add boto3 supabase` — cloud dependencies installed
- [ ] `SyncSettings` reads from environment variables
- [ ] `upload_file()` skips files already in bucket (HEAD check)
- [ ] `push_metadata()` upserts to Supabase in batches of 500
- [ ] `pull_metadata()` merges by SHA-256 (no duplicates)
- [ ] Conflict resolution: last-write-wins by `updated_at`
- [ ] `uv run samplemind sync status` shows config without crashing
- [ ] `uv run samplemind sync push --no-files` pushes only metadata
- [ ] All tests pass with mocked S3 and Supabase
- [ ] Feature flag `cloud_sync` gates the feature
- [ ] Device ID is stable (based on MAC address, not random)

