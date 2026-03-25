# Phase 13 Agent — Cloud Sync & Multi-Device

Handles: S3/R2 file sync, Supabase metadata sync, conflict resolution, multi-device library management.

## Triggers
Phase 13, cloud sync, R2, S3, Supabase, multi-device, `sync push`, `sync pull`, boto3, `SyncSettings`, `push_metadata`, `src/samplemind/sync/`, "sync my library", "multi-device", "cloud backup"

**File patterns:** `src/samplemind/sync/**/*.py`

**Code patterns:** `import boto3`, `s3.head_object`, `SyncSettings`, `push_metadata`, `supabase`

## Key Files
```
src/samplemind/sync/
  settings.py    — SyncSettings (R2 credentials, Supabase URL)
  r2_client.py   — Cloudflare R2 file sync (boto3 S3 API)
  supabase_client.py — metadata sync (supabase-py)
  conflict.py    — last-write-wins conflict resolution
  cli.py         — CLI: samplemind sync push/pull/status
```

## Technology Stack
| Component | Technology |
|-----------|-----------|
| File storage | Cloudflare R2 (S3-compatible), or AWS S3, Backblaze B2 |
| S3 client | boto3 |
| Metadata | Supabase (PostgreSQL) |
| Conflict strategy | Last-write-wins by `updated_at` |
| Deduplication | SHA-256 of first 64KB (same as fingerprint.py) |
| Feature flag | `cloud_sync` |

## CLI Commands
```bash
uv run samplemind sync push            # upload new/changed samples to R2
uv run samplemind sync pull            # download changes from R2
uv run samplemind sync status          # show pending changes
```

## Rules
1. Feature gated by `get_settings().cloud_sync`
2. R2/S3 credentials via env vars only — never hardcoded
3. SHA-256 deduplication before every upload — skip already-uploaded files
4. Conflict resolution: last-write-wins by `updated_at` timestamp
5. All sync operations must support `--dry-run` flag

