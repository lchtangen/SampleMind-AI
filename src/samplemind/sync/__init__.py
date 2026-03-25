"""Multi-device library sync via Cloudflare R2, Supabase, or S3-compatible storage.

Phase 13 — Cloud Sync.
Synchronises both audio files (object storage: R2/S3/B2) and library
metadata (Supabase Postgres or SQLite CRDT merge). Supports push, pull,
and bidirectional sync with conflict resolution via last-write-wins timestamps.

See: docs/en/phase-13-cloud-sync.md
"""
