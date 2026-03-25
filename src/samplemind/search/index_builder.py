"""Batch index rebuild pipeline: iterate library, embed, store in VectorIndex.

Phase 11 — Semantic Search.
Reads all Sample rows from SampleRepository, calls embed_audio() on each
file path, and upserts the resulting vector into the VectorIndex. Supports
incremental updates (only re-embed samples whose embedding is missing or
whose fingerprint has changed since last index build).
"""
# TODO: implement in Phase 11 — Semantic Search
