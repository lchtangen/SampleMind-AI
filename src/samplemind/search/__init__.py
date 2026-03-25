"""CLAP audio embeddings and sqlite-vec vector search for semantic similarity.

Phase 11 — Semantic Search.
Enables "find samples that sound like this" queries using audio embeddings
from a CLAP model (Contrastive Language-Audio Pre-training). Embeddings are
stored in a sqlite-vec virtual table and searched via cosine similarity.

See: docs/en/phase-11-semantic-search.md
"""
