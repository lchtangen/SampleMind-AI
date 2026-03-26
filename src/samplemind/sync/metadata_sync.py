"""Supabase metadata push/pull with last-write-wins CRDT merge.

Phase 13 — Cloud Sync.
Serialises Sample rows to JSON and syncs them with a Supabase Postgres table.
push_metadata() upserts local changes; pull_metadata() fetches remote rows and
merges using imported_at timestamp (remote wins on conflict unless local is newer).

Install:
    uv sync --extra sync   # adds supabase>=2

Environment variables:
    SAMPLEMIND_SUPABASE_URL  — project URL, e.g. https://xxx.supabase.co
    SAMPLEMIND_SUPABASE_KEY  — anon or service-role key
"""

from __future__ import annotations

import contextlib
from datetime import UTC
import logging
import os

logger = logging.getLogger(__name__)


def _require_supabase() -> object:
    """Return the supabase module or raise ImportError with install hint."""
    try:
        from supabase import create_client  # type: ignore[import-untyped]

        return create_client
    except ImportError as exc:
        raise ImportError(
            "supabase is not installed. "
            "Run: uv sync --extra sync\n"
            "Or:  pip install 'supabase>=2'"
        ) from exc


def _get_client() -> object:
    """Build a Supabase client from environment variables."""
    create_client = _require_supabase()
    url = os.environ.get("SAMPLEMIND_SUPABASE_URL", "")
    key = os.environ.get("SAMPLEMIND_SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SAMPLEMIND_SUPABASE_URL and SAMPLEMIND_SUPABASE_KEY must be set."
        )
    return create_client(url, key)  # type: ignore[operator]


def push_metadata(settings: object | None = None) -> dict[str, int]:
    """Upsert all local Sample rows to Supabase Postgres.

    Reads every row from the local SQLite ``samples`` table and upserts
    them (by ``path``) into the remote ``samples`` table in Supabase.

    Args:
        settings: Unused — reserved for future ``SyncSettings`` integration.

    Returns:
        ``{"upserted": N, "errors": M}``

    Raises:
        ImportError: If supabase is not installed.
        RuntimeError: If Supabase env vars are not set.
    """
    from samplemind.data.orm import init_orm
    from samplemind.data.repositories.sample_repository import SampleRepository

    init_orm()
    client = _get_client()

    samples = SampleRepository.search()  # all rows
    upserted = 0
    errors = 0

    for sample in samples:
        row = {
            "filename": sample.filename,
            "path": sample.path,
            "bpm": sample.bpm,
            "key": sample.key,
            "mood": sample.mood,
            "energy": sample.energy,
            "instrument": sample.instrument,
            "genre": sample.genre,
            "tags": sample.tags,
            "imported_at": sample.imported_at.isoformat() if sample.imported_at else None,
        }
        try:
            client.table("samples").upsert(row, on_conflict="path").execute()  # type: ignore[union-attr]
            upserted += 1
        except Exception:
            logger.exception("Failed to upsert sample path=%s", sample.path)
            errors += 1

    logger.info("push_metadata: upserted=%d errors=%d", upserted, errors)
    return {"upserted": upserted, "errors": errors}


def pull_metadata(settings: object | None = None) -> dict[str, int]:
    """Fetch remote Sample rows and merge with the local library.

    Uses a last-write-wins strategy: if the remote ``imported_at`` is newer
    than the local value, the local row is updated.  New remote rows (not in
    local SQLite) are inserted as new samples.

    Args:
        settings: Unused — reserved for future ``SyncSettings`` integration.

    Returns:
        ``{"merged": N, "inserted": M, "errors": K}``

    Raises:
        ImportError: If supabase is not installed.
        RuntimeError: If Supabase env vars are not set.
    """
    from datetime import datetime

    from samplemind.core.models.sample import SampleCreate, SampleUpdate
    from samplemind.data.orm import init_orm
    from samplemind.data.repositories.sample_repository import SampleRepository

    init_orm()
    client = _get_client()

    response = client.table("samples").select("*").execute()  # type: ignore[union-attr]
    remote_rows: list[dict[str, object]] = getattr(response, "data", [])

    merged = inserted = errors = 0

    for row in remote_rows:
        path = str(row.get("path", ""))
        if not path:
            errors += 1
            continue

        try:
            existing = SampleRepository.get_by_path(path)
        except Exception:
            existing = None

        remote_ts_raw = row.get("imported_at")
        remote_ts: datetime | None = None
        if isinstance(remote_ts_raw, str):
            with contextlib.suppress(ValueError):
                remote_ts = datetime.fromisoformat(remote_ts_raw).replace(
                    tzinfo=UTC
                )

        try:
            if existing is None:
                SampleRepository.upsert(
                    SampleCreate(
                        filename=str(row.get("filename", "")),
                        path=path,
                        bpm=row.get("bpm"),
                        key=row.get("key"),
                        mood=row.get("mood"),
                        energy=row.get("energy"),
                        instrument=row.get("instrument"),
                        genre=row.get("genre"),
                        tags=row.get("tags"),
                    )
                )
                inserted += 1
            else:
                local_ts = existing.imported_at
                if remote_ts and (local_ts is None or remote_ts > local_ts):
                    SampleRepository.tag(
                        path,
                        SampleUpdate(
                            genre=row.get("genre"),
                            tags=row.get("tags"),
                        ),
                    )
                    merged += 1
        except Exception:
            logger.exception("Failed to merge remote sample path=%s", path)
            errors += 1

    logger.info("pull_metadata: merged=%d inserted=%d errors=%d", merged, inserted, errors)
    return {"merged": merged, "inserted": inserted, "errors": errors}
