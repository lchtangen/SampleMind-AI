"""sqlite-vec or FAISS vector index wrapper for nearest-neighbour search.

Phase 11 — Semantic Search.
Provides VectorIndex: a thin abstraction over the sqlite-vec virtual table
(preferred, no native code) with optional FAISS fallback for large libraries.
Supports upsert(sample_id, embedding), search(embedding, k=10), and delete().
"""
# TODO: implement in Phase 11 — Semantic Search
