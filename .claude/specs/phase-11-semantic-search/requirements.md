# Phase 11 — Semantic Search Requirements

**Feature:** CLAP Embeddings + FAISS Vector Search
**Status:** Draft — ready for spec design phase
**Created:** 2026-03-26

---

## Overview

Augment the existing text/filter search with semantic vector search using CLAP (Contrastive
Language-Audio Pre-training) embeddings and a FAISS index. Users can search by natural
language description ("dark aggressive 808 bass at 140 BPM") and get results ranked by
audio-semantic similarity rather than exact keyword match.

---

## Functional Requirements (EARS Format)

### Embedding Computation

- WHEN a new sample is imported via `samplemind import`, THE SYSTEM SHALL compute a CLAP audio embedding for the WAV file and store it in the database.
- WHEN the `--skip-embeddings` flag is passed to import, THE SYSTEM SHALL skip embedding computation (fast mode for large batch imports).
- WHEN `samplemind embed --all` is run, THE SYSTEM SHALL compute embeddings for all samples that currently have none (backfill mode).
- THE SYSTEM SHALL store embeddings as a binary blob in the `sample_embeddings` table, linked by sample ID.

### FAISS Index

- WHEN embeddings are available for at least 10 samples, THE SYSTEM SHALL build a FAISS flat L2 index from all stored embeddings.
- THE SYSTEM SHALL persist the FAISS index to disk at the path configured by `get_settings().embeddings_index_path`.
- WHEN the index file exists on startup, THE SYSTEM SHALL load it automatically without rebuilding.
- WHEN new embeddings are added (import), THE SYSTEM SHALL mark the index as stale and rebuild it lazily on the next search.

### Semantic Search

- WHEN the user runs `samplemind search --semantic "dark aggressive bass"`, THE SYSTEM SHALL encode the query text using the CLAP text encoder and perform a FAISS top-K search.
- THE SYSTEM SHALL return the top 20 results by default, configurable via `--limit N`.
- THE SYSTEM SHALL support combining semantic search with filter constraints: `--semantic "bass" --energy high --bpm-min 130`.
- WHEN `--json` is passed, THE SYSTEM SHALL include a `similarity_score` field (0.0–1.0) in each result.

### CLI Interface

- THE SYSTEM SHALL add a `--semantic <query>` flag to the existing `samplemind search` command.
- THE SYSTEM SHALL add a `samplemind embed` subcommand with `--all`, `--sample-id`, and `--status` subflags.
- WHEN `samplemind embed --status` is run, THE SYSTEM SHALL report: total samples, samples with embeddings, samples without, index staleness.

### API Interface

- THE SYSTEM SHALL add a `GET /api/v1/search/semantic?q=<query>&limit=N` endpoint to the FastAPI server.
- THE SYSTEM SHALL add a `POST /api/v1/embed` endpoint that triggers background embedding for a sample ID.

### Performance

- Embedding computation per file SHALL complete within 2 seconds on CPU (no GPU required).
- FAISS search over 10,000 samples SHALL complete within 100ms.
- Index rebuild for 1,000 samples SHALL complete within 10 seconds.

---

## Non-Functional Requirements

- CLAP model weights are downloaded on first use and cached at `~/.cache/samplemind/clap/`.
- Embedding computation is optional — system works fully without it (falls back to keyword search).
- FAISS index is rebuilt automatically when >10% of samples lack embeddings.
- The `VectorIndex` class must be thread-safe (used by both CLI and web server).

---

## Out of Scope (Phase 11)

- GPU-accelerated FAISS (CPU only for Phase 11)
- Real-time embedding during audio recording
- Cross-library similarity (comparing samples across different SampleMind instances)
- Embedding fine-tuning on user data

---

## Key Files

| File | Purpose |
|------|---------|
| `src/samplemind/search/embeddings.py` | CLAP encoder wrapper, embedding storage |
| `src/samplemind/search/vector_index.py` | FAISS index build/load/query |
| `src/samplemind/search/semantic_search.py` | Combined text+filter search |
| `src/samplemind/core/models/sample.py` | Add `embedding` field to SampleEmbedding table |
| `migrations/versions/` | Migration for `sample_embeddings` table |

---

*Next step: run KFC spec design phase — `spec-design` agent will create `design.md`*
