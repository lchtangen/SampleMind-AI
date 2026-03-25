# Skill: semantic-search

Find audio samples by natural language description or audio similarity using CLAP embeddings and FAISS vector search.

## Commands

```bash
# Text search
uv run samplemind semantic "dark atmospheric pad"
uv run samplemind semantic "punchy trap kick" --top 20
uv run samplemind semantic "lo-fi chill" --min-score 0.7 --json

# Audio reference search
uv run samplemind semantic --audio ~/Music/reference.wav --top 10

# Rebuild FAISS index (required after bulk import)
uv run samplemind index rebuild --workers 4
uv run samplemind index rebuild --json

# API
curl "http://localhost:8000/api/v1/search/semantic?q=dark+bass&top=20"
```

## Key Files

```
src/samplemind/search/
  embeddings.py      # embed_audio(), embed_text() — L2-normalized 512-dim
  vector_index.py    # VectorIndex, get_vector_index()
  index_builder.py   # rebuild_index(), incremental add_batch()
  chromadb_store.py  # ChromaDB alternative for hybrid search

src/samplemind/cli/commands/semantic_cmd.py
src/samplemind/api/routes/semantic.py
tests/test_semantic_search.py
```

## Embedding Contract

- **Dimension:** 512 (CLAP 2023 model from msclap)
- **Normalization:** L2-normalized unit vectors (always)
- **Similarity:** cosine = dot product (0.0 unrelated → 1.0 identical)
- **Practical threshold:** ≥ 0.75 for "similar" samples
- **Dtype:** float32
- **Index file:** `~/.samplemind/vector_index.faiss`

## Feature Flag

```python
from samplemind.core.feature_flags import is_enabled
if not is_enabled("semantic_search"):
    # show upgrade message
```

Enable: `echo '{"semantic_search": {"enabled": true}}' > ~/.samplemind/flags.json`

## Testing

```bash
# Fast (mocked CLAP — no downloads)
uv run pytest tests/test_semantic_search.py -m "not slow" -v

# Slow (real CLAP — downloads ~900MB on first run)
uv run pytest tests/test_semantic_search.py -m slow -v
```

**Rule:** Never load the real CLAP model in unit tests. Mock `embed_audio` and `embed_text`.

## Dependencies

```bash
uv add faiss-cpu msclap sentence-transformers numpy
# GPU (for libraries > 100k samples):
# uv add faiss-gpu
```

