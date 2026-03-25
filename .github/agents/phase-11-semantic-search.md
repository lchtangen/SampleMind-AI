# Phase 11 Agent — Semantic Search

Handles: CLAP embeddings, FAISS vector index, ChromaDB, text-to-audio search, audio-to-audio search.

## Triggers
- Phase 11, CLAP, FAISS, vector index, semantic search, cosine similarity, ChromaDB, msclap, text-to-audio, audio similarity

## Key Files
- `src/samplemind/search/embeddings.py`
- `src/samplemind/search/vector_index.py`
- `src/samplemind/search/index_builder.py`
- `src/samplemind/search/chromadb_store.py`
- `src/samplemind/cli/commands/semantic_cmd.py`
- `src/samplemind/api/routes/semantic.py`

## Embedding Contract

- Dimension: 512 (CLAP 2023)
- Dtype: float32
- Normalization: L2-normalized unit vectors (ALWAYS)
- Similarity: cosine = dot product
- Score range: 0.0 → 1.0 (practical "similar": ≥ 0.75)

## Feature Flag

```python
if not is_enabled("semantic_search"):
    raise HTTPException(503, "Semantic search not yet available")
```

## Rules
1. ALL embeddings L2-normalized before adding to FAISS
2. CLAP model loads lazily — never at module import time
3. Feature flag gates CLI, API, and Svelte UI
4. Index rebuilt after every batch import
5. Mock `embed_audio`/`embed_text` in ALL unit tests (no CLAP downloads in CI)
6. FAISS returns `-1` for empty slots — always filter `idx >= 0`
7. ChromaDB distances are `1 - cosine`; convert: `score = 1.0 - distance`

