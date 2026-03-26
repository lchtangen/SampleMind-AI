"""Tests for Phase 13 Cloud Sync.

All boto3 network calls are replaced by MagicMock — no cloud account required.
Tests verify push_files(), pull_files(), and SyncSettings behavior.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from samplemind.sync.config import SyncSettings
from samplemind.sync.file_sync import _md5_hex, pull_files, push_files

# ── helpers ───────────────────────────────────────────────────────────────────


def _settings(**overrides: object) -> SyncSettings:
    """Return SyncSettings with safe test defaults, overridable per-test."""
    return SyncSettings(
        endpoint_url="https://test.r2.cloudflarestorage.com",
        bucket="test-bucket",
        prefix="samples/",
        access_key="test-key",
        secret_key="test-secret",
        region="auto",
        **overrides,
    )


def _wav(path: Path) -> Path:
    """Write a minimal RIFF payload and return the path."""
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    return path


# ── _md5_hex ──────────────────────────────────────────────────────────────────


def test_md5_hex_matches_hashlib(tmp_path: Path) -> None:
    f = _wav(tmp_path / "a.wav")
    assert _md5_hex(f) == hashlib.md5(f.read_bytes(), usedforsecurity=False).hexdigest()
    assert len(_md5_hex(f)) == 32


# ── push_files ────────────────────────────────────────────────────────────────


def test_push_files_uploads_new_file(tmp_path: Path) -> None:
    """File with no remote counterpart → upload_file called, uploaded=1."""
    wav = _wav(tmp_path / "kick.wav")
    mock_client = MagicMock()
    mock_client.head_object.side_effect = Exception("NoSuchKey")

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = push_files([wav], settings=_settings())

    mock_client.upload_file.assert_called_once()
    assert result == {"uploaded": 1, "skipped": 0, "errors": 0}


def test_push_files_skips_matching_etag(tmp_path: Path) -> None:
    """Local MD5 matches remote ETag → skipped, no upload_file call."""
    wav = _wav(tmp_path / "kick.wav")
    local_md5 = _md5_hex(wav)
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ETag": f'"{local_md5}"'}

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = push_files([wav], settings=_settings())

    mock_client.upload_file.assert_not_called()
    assert result == {"uploaded": 0, "skipped": 1, "errors": 0}


def test_push_files_dry_run_no_upload(tmp_path: Path) -> None:
    """dry_run=True → no upload_file call; uploaded counts what would-be-uploaded."""
    wav = _wav(tmp_path / "kick.wav")
    mock_client = MagicMock()
    mock_client.head_object.side_effect = Exception("NoSuchKey")

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = push_files([wav], settings=_settings(dry_run=True))

    mock_client.upload_file.assert_not_called()
    assert result["uploaded"] == 1  # dry run counts as "would upload"
    assert result["errors"] == 0


def test_push_files_missing_file_is_error(tmp_path: Path) -> None:
    """Non-existent file → errors=1; no upload attempted."""
    ghost = tmp_path / "ghost.wav"
    mock_client = MagicMock()

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = push_files([ghost], settings=_settings())

    mock_client.upload_file.assert_not_called()
    assert result == {"uploaded": 0, "skipped": 0, "errors": 1}


def test_push_files_result_keys(tmp_path: Path) -> None:
    """Result dict always contains exactly 'uploaded', 'skipped', 'errors'."""
    mock_client = MagicMock()

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = push_files([], settings=_settings())

    assert set(result) == {"uploaded", "skipped", "errors"}


# ── pull_files ────────────────────────────────────────────────────────────────


def _mock_paginator(keys: list[str]) -> MagicMock:
    """Return a mock paginator that yields one page with the given S3 keys."""
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{"Contents": [{"Key": k} for k in keys]}]
    return mock_paginator


def test_pull_files_downloads_missing(tmp_path: Path) -> None:
    """Remote key absent locally → download_file called, downloaded=1."""
    mock_client = MagicMock()
    mock_client.get_paginator.return_value = _mock_paginator(["samples/kick.wav"])

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = pull_files(tmp_path, settings=_settings())

    mock_client.download_file.assert_called_once()
    assert result == {"downloaded": 1, "skipped": 0, "errors": 0}


def test_pull_files_skips_existing(tmp_path: Path) -> None:
    """File already present locally → skipped, no download_file call."""
    _wav(tmp_path / "kick.wav")  # pre-create the file
    mock_client = MagicMock()
    mock_client.get_paginator.return_value = _mock_paginator(["samples/kick.wav"])

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = pull_files(tmp_path, settings=_settings())

    mock_client.download_file.assert_not_called()
    assert result == {"downloaded": 0, "skipped": 1, "errors": 0}


def test_pull_files_dry_run_no_download(tmp_path: Path) -> None:
    """dry_run=True → no download_file call; downloaded counts what would-be-downloaded."""
    mock_client = MagicMock()
    mock_client.get_paginator.return_value = _mock_paginator(["samples/snare.wav"])

    with patch("samplemind.sync.file_sync._make_client", return_value=mock_client):
        result = pull_files(tmp_path, settings=_settings(dry_run=True))

    mock_client.download_file.assert_not_called()
    assert result["downloaded"] == 1  # dry run counts as "would download"
    assert result["errors"] == 0


# ── SyncSettings ──────────────────────────────────────────────────────────────


def test_sync_settings_defaults() -> None:
    """Default values are correct without any environment variables."""
    s = SyncSettings()
    assert s.endpoint_url == "https://s3.amazonaws.com"
    assert s.bucket == "samplemind-library"
    assert s.prefix == "samples/"
    assert s.dry_run is False
    assert s.region == "auto"


def test_sync_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """SAMPLEMIND_SYNC_* env vars override defaults."""
    monkeypatch.setenv("SAMPLEMIND_SYNC_BUCKET", "my-custom-bucket")
    monkeypatch.setenv("SAMPLEMIND_SYNC_DRY_RUN", "true")
    s = SyncSettings()
    assert s.bucket == "my-custom-bucket"
    assert s.dry_run is True
