# Phase 11 Agent — Semantic Search & Vector Embeddings

Handles: CLAP embeddings, FAISS vector indexing, ChromaDB, text-to-audio and audio-to-audio similarity search.

## Triggers
Phase 11, CLAP, FAISS, ChromaDB, vector index, cosine similarity, semantic search, `embed_audio`, `embed_text`, `VectorIndex`, `src/samplemind/search/`, "find similar samples", "semantic search", "text to audio search"

**File patterns:** `src/samplemind/search/**/*.py`

**Code patterns:** `import faiss`, `CLAP`, `embed_audio`, `embed_text`, `VectorIndex`, `cosine_similarity`

## Key Files
```
src/samplemind/search/
  embeddings.py   — CLAP model wrapper, embed_audio(), embed_text()
  vector_store.py — FAISS IndexFlatIP, add/search/save/load
  index.py        — VectorIndex: orchestrates embeddings + FAISS
  cli.py          — CLI: samplemind semantic "query" --top 20
```

## Technology Stack
| Component | Technology |
|-----------|-----------|
| Embeddings | CLAP (LAION-AI/CLAP via msclap) — 512-dim |
| Vector index | FAISS IndexFlatIP — exact cosine search |
| Persistent alt | ChromaDB — hybrid vector+metadata |
| Feature flag | `semantic_search` — gates the feature |

## Embedding Pattern
```python
# Audio → vector
embedding = embed_audio(path)              # 512-dim np.ndarray, L2-normalized
# Text → vector
embedding = embed_text("dark trap kick")   # same 512-dim space as audio
# Search
results = vector_store.search(embedding, top_k=20)
```

## CLI Commands
```bash
uv run samplemind semantic "dark atmospheric pad" --top 20
uv run samplemind index rebuild             # rebuild FAISS from all DB samples
uv run samplemind index add <path>          # add single sample to index
```

## Rules
1. Feature gated by `get_settings().semantic_search` — check before any CLAP/FAISS import
2. CLAP model weights: downloaded on first use, cached in `~/.cache/samplemind/models/`
3. FAISS index: saved to `~/Library/Application Support/SampleMind/faiss.index`
4. All vectors must be L2-normalized before indexing (IndexFlatIP = dot product = cosine)
5. Mock backend must be available for tests (no GPU/model download required)

