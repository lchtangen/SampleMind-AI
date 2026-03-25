"""Supabase metadata push/pull with last-write-wins CRDT merge.

Phase 13 — Cloud Sync.
Serialises Sample rows to JSON and syncs them with a Supabase Postgres table.
push_metadata() upserts local changes; pull_metadata() fetches remote rows and
merges using updated_at timestamp (remote wins on conflict unless local is newer).
"""
# TODO: implement in Phase 13 — Cloud Sync
