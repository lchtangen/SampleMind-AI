# Phase 13 Agent — Cloud Sync

Handles: Cloudflare R2, boto3, Supabase, multi-device sync, SHA-256 deduplication.

## Triggers
- Phase 13, cloud sync, Cloudflare R2, S3, boto3, Supabase, multi-device, sync push, sync pull, signed URL

## Key Files
- `src/samplemind/sync/config.py`
- `src/samplemind/sync/file_sync.py`
- `src/samplemind/sync/metadata_sync.py`
- `src/samplemind/cli/commands/sync_cmd.py`

## S3 Key Format

```
{prefix}/audio/{sha256[:2]}/{sha256}.wav
```
Example: `user_abc/audio/a3/a3f2b1...wav`

## Sync Protocol

```
push:  SHA-256 → HeadObject → skip if exists → upload_file()
pull:  fetch Supabase records from other devices → merge by sha256
dedup: same sha256 = same file, never duplicate
```

## Rules
1. ALWAYS HeadObject before upload (idempotent sync)
2. NEVER auto-delete remote files — sync is additive only
3. SHA-256 of first 64KB (matches `fingerprint.py`)
4. All S3/Supabase calls mocked in tests — no cloud access in CI
5. Device ID: stable MAC-address-based (not random UUID)
6. Supabase upsert: max 500 records per batch
7. Feature flag `cloud_sync` gates all commands
8. Download signed URLs: 24h expiry; preview URLs: 1h expiry

