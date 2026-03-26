# Phase 11 — Semantic Search & Vector Embeddings

**Status: 📋 Planned — Spec ready** | Phase 11 of 16 | Agent: `phase-11-semantic-search`
Spec: [`.claude/specs/phase-11-semantic-search/requirements.md`](../../.claude/specs/phase-11-semantic-search/requirements.md)

> **Goal:** Find samples by sound similarity and natural language description.
> "Find samples that sound like rain on a metal roof" — and get results in < 100 ms.
>
> **Stack:** CLAP (Contrastive Language-Audio Pretraining) · FAISS vector index ·
> ChromaDB (persistent) · SentenceTransformers for text · numpy for similarity math.
>
> **Prerequisites:** Phase 2 (audio analysis), Phase 3 (database), Phase 5 (web UI).

---

## 1. Overview and Architecture

```
User query (text or audio)
        │
        ▼
  EmbeddingService
  ┌─────────────┐
  │ Text query  │→ CLAP text encoder → 512-dim vector
  │ Audio query │→ CLAP audio encoder→ 512-dim vector
  └─────────────┘
        │
        ▼
  VectorIndex (FAISS)
  ┌──────────────────────────────────────┐
  │ IndexFlatIP (inner product / cosine) │
  │ 512-dim × N samples                  │
  │ Rebuilt on import, persisted to disk │
  └──────────────────────────────────────┘
        │
        ▼
  Top-K results (sample IDs + similarity scores)
        │
        ▼
  Enrich from SQLite (metadata, path, BPM, key)
        │
        ▼
  JSON response → CLI / Web / Tauri / Plugin
```

CLAP maps both audio and text into the same 512-dimensional embedding space,
meaning "dark bass" (text) and a dark bass sample (audio) have high cosine similarity.

---

## 2. Install Dependencies

```bash
uv add faiss-cpu sentence-transformers msclap numpy
# GPU (optional — FAISS-GPU for large libraries >100k samples):
# uv add faiss-gpu
```

```toml
# pyproject.toml extras
[project.optional-dependencies]
semantic = ["faiss-cpu", "sentence-transformers", "msclap", "numpy"]
```

---

## 3. CLAP Embedding Service

```python
# src/samplemind/search/embeddings.py
"""
Audio and text embedding service using CLAP (LAION-AI/CLAP).

CLAP maps audio and text into the SAME 512-dimensional space.
Cosine similarity between any (audio, text) or (audio, audio) pair.

Model loading is lazy (first call) and cached in memory.
The model file (~900 MB) is downloaded to ~/.cache/huggingface/ on first use.

Embedding contract:
  - All embeddings are L2-normalized (unit vectors)
  - Cosine similarity = dot product of unit vectors
  - Score range: 0.0 (unrelated) → 1.0 (identical)
  - Practical threshold for "similar": > 0.75

Performance:
  - CPU: ~50 ms per audio file (22050 Hz, 5s)
  - M2 Mac (MPS): ~8 ms per file
  - Batch of 100 files: ~2s on CPU, ~200ms on MPS
"""
from __future__ import annotations
import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

_clap_model = None


def _get_model():
    """Lazy-load CLAP model. Downloads ~900MB on first call."""
    global _clap_model
    if _clap_model is None:
        from msclap import CLAP
        # Use CLAP 2023 model (best audio-text alignment)
        _clap_model = CLAP(version="2023", use_cuda=_has_cuda())
    return _clap_model


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def embed_audio(path: Path) -> np.ndarray:
    """
    Compute 512-dim CLAP embedding for a WAV/AIFF file.

    Args:
        path: Path to audio file (WAV/AIFF, any sample rate — CLAP resamples)

    Returns:
        L2-normalized numpy array, shape (512,), dtype float32
    """
    model = _get_model()
    embeddings = model.get_audio_embeddings([str(path)], resample=True)
    vec = np.array(embeddings[0], dtype=np.float32)
    return vec / (np.linalg.norm(vec) + 1e-10)   # L2-normalize


def embed_text(query: str) -> np.ndarray:
    """
    Compute 512-dim CLAP embedding for a text query.

    Example queries:
      "dark atmospheric pad"
      "punchy 808 kick with sub"
      "hi-hat with swing and ghost notes"
      "rain on metal roof"

    Returns:
        L2-normalized numpy array, shape (512,), dtype float32
    """
    model = _get_model()
    embeddings = model.get_text_embeddings([query])
    vec = np.array(embeddings[0], dtype=np.float32)
    return vec / (np.linalg.norm(vec) + 1e-10)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two L2-normalized vectors. Range [0, 1]."""
    return float(np.clip(np.dot(a, b), 0.0, 1.0))
```

---

## 4. FAISS Vector Index

```python
# src/samplemind/search/vector_index.py
"""
FAISS vector index for sample library similarity search.

Index type: IndexFlatIP (exact inner product search on unit vectors = cosine)
For libraries > 100k samples, upgrade to IndexIVFFlat with nlist=256.

Index file: ~/.samplemind/vector_index.faiss
ID map file: ~/.samplemind/vector_index_ids.npy

The ID map maps FAISS row indices → SQLite sample IDs.
Always rebuild the index after a batch import.

Performance:
  - Search 10k samples: < 1ms (CPU, IndexFlatIP)
  - Search 100k samples: ~5ms (CPU, IndexFlatIP)
  - Search 1M samples: use IndexIVFFlat with GPU
"""
from __future__ import annotations
import numpy as np
import faiss
from pathlib import Path
from dataclasses import dataclass

INDEX_DIM   = 512    # CLAP embedding dimension
INDEX_PATH  = Path.home() / ".samplemind" / "vector_index.faiss"
IDS_PATH    = Path.home() / ".samplemind" / "vector_index_ids.npy"


@dataclass
class SearchResult:
    sample_id: int
    score: float      # cosine similarity [0, 1]
    rank: int


class VectorIndex:
    """
    Wrapper around FAISS IndexFlatIP for sample similarity search.

    Thread-safe for reads. Writes (add_batch, rebuild) should be
    called from a single background thread.
    """

    def __init__(self) -> None:
        self._index: faiss.IndexFlatIP | None = None
        self._ids: np.ndarray | None = None   # shape (N,), dtype int64

    def load(self) -> bool:
        """Load index from disk. Returns False if no index exists."""
        if not INDEX_PATH.exists():
            return False
        self._index = faiss.read_index(str(INDEX_PATH))
        self._ids   = np.load(str(IDS_PATH))
        return True

    def save(self) -> None:
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(INDEX_PATH))
        np.save(str(IDS_PATH), self._ids)

    def build(self, sample_ids: list[int], embeddings: np.ndarray) -> None:
        """
        Build index from scratch.

        Args:
            sample_ids:  List of SQLite sample IDs, length N
            embeddings:  Array of L2-normalized vectors, shape (N, 512)
        """
        self._index = faiss.IndexFlatIP(INDEX_DIM)
        self._index.add(embeddings.astype(np.float32))
        self._ids = np.array(sample_ids, dtype=np.int64)
        self.save()

    def add_batch(self, new_ids: list[int], new_embeddings: np.ndarray) -> None:
        """Add new samples to existing index (incremental update)."""
        if self._index is None:
            self.build(new_ids, new_embeddings)
            return
        self._index.add(new_embeddings.astype(np.float32))
        self._ids = np.concatenate([self._ids, np.array(new_ids, dtype=np.int64)])
        self.save()

    def search(self, query_vector: np.ndarray, top_k: int = 20) -> list[SearchResult]:
        """
        Find the top-K most similar samples.

        Args:
            query_vector: L2-normalized embedding, shape (512,)
            top_k:        Number of results to return

        Returns:
            List of SearchResult sorted by score descending
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        q = query_vector.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(q, min(top_k, self._index.ntotal))

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < 0:  # FAISS returns -1 for empty slots
                break
            results.append(SearchResult(
                sample_id=int(self._ids[idx]),
                score=float(np.clip(score, 0.0, 1.0)),
                rank=rank,
            ))
        return results


# Singleton instance
_index_instance: VectorIndex | None = None

def get_vector_index() -> VectorIndex:
    global _index_instance
    if _index_instance is None:
        _index_instance = VectorIndex()
        _index_instance.load()
    return _index_instance
```

---

## 5. Semantic Search CLI Command

```python
# src/samplemind/cli/commands/semantic_cmd.py
"""
Semantic search command — find samples by text or audio similarity.

Examples:
  uv run samplemind semantic "dark atmospheric pad"
  uv run samplemind semantic "punchy trap kick" --top 20
  uv run samplemind semantic --audio ~/Music/reference.wav --top 10
  uv run samplemind semantic "lo-fi chill" --min-score 0.7 --json
"""
import json
import sys
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Semantic similarity search")
console = Console(stderr=True)


@app.command()
def semantic(
    query: str = typer.Argument(None, help="Text description of desired sound"),
    audio: str = typer.Option(None, "--audio", "-a", help="Reference audio file path"),
    top: int = typer.Option(10, "--top", "-k", help="Number of results"),
    min_score: float = typer.Option(0.0, "--min-score", help="Minimum similarity score 0–1"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Find samples by text description or audio similarity using CLAP embeddings."""
    from samplemind.core.feature_flags import is_enabled
    if not is_enabled("semantic_search"):
        console.print("[yellow]Semantic search is not yet enabled.[/yellow]")
        console.print("Enable: echo '{\"semantic_search\": {\"enabled\": true}}' > ~/.samplemind/flags.json")
        raise typer.Exit(1)

    from samplemind.search.embeddings import embed_text, embed_audio
    from samplemind.search.vector_index import get_vector_index
    from samplemind.data.repositories.sample_repository import SampleRepository

    if audio:
        console.print(f"[cyan]Encoding reference audio:[/cyan] {audio}")
        vec = embed_audio(Path(audio).expanduser())
    elif query:
        console.print(f"[cyan]Encoding query:[/cyan] {query!r}")
        vec = embed_text(query)
    else:
        console.print("[red]Provide a query string or --audio reference file[/red]")
        raise typer.Exit(1)

    idx = get_vector_index()
    hits = idx.search(vec, top_k=top)
    hits = [h for h in hits if h.score >= min_score]

    # Enrich with metadata from SQLite
    results = []
    for hit in hits:
        sample = SampleRepository.get_by_id(hit.sample_id)
        if sample:
            results.append({**sample.model_dump(), "similarity": round(hit.score, 4), "rank": hit.rank})

    if json_output:
        print(json.dumps(results, indent=2))
        return

    # Rich table output
    table = Table(title=f"Semantic Search: {query or audio}")
    table.add_column("#",          style="dim", width=3)
    table.add_column("Score",      style="cyan", width=6)
    table.add_column("Filename",   style="bold")
    table.add_column("Instrument", style="green")
    table.add_column("BPM",        width=6)
    table.add_column("Key",        width=8)
    table.add_column("Mood")

    for r in results:
        table.add_row(
            str(r["rank"] + 1),
            f"{r['similarity']:.3f}",
            r["filename"],
            r.get("instrument", ""),
            str(r.get("bpm", "")),
            r.get("key", ""),
            r.get("mood", ""),
        )
    console.print(table)
```

---

## 6. Index Building — After Batch Import

```python
# src/samplemind/search/index_builder.py
"""
Rebuild or update the FAISS vector index after batch import.

Called automatically by the import pipeline after analysis is complete.
Also available as a CLI command:
  uv run samplemind index rebuild
  uv run samplemind index update   # incremental — only add new samples
"""
from __future__ import annotations
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.search.embeddings import embed_audio
from samplemind.search.vector_index import VectorIndex
from samplemind.core.logging import get_logger

log = get_logger(__name__)


def rebuild_index(workers: int = 4) -> dict:
    """
    Rebuild the entire FAISS index from scratch.

    Reads all sample paths from SQLite, embeds each with CLAP,
    builds a new IndexFlatIP. Safe to run while the app is running
    — old index remains available until the new one is saved.

    Returns:
        {"samples": N, "elapsed_s": T, "index_size_mb": M}
    """
    import time
    start = time.perf_counter()

    samples = SampleRepository.get_all()
    log.info("index_rebuild_start", sample_count=len(samples))

    ids: list[int] = []
    vecs: list[np.ndarray] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("Embedding samples...", total=len(samples))

        def embed_one(sample):
            try:
                vec = embed_audio(Path(sample.path))
                return sample.id, vec
            except Exception as e:
                log.warning("embed_failed", path=sample.path, error=str(e))
                return None

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(embed_one, s): s for s in samples}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    ids.append(result[0])
                    vecs.append(result[1])
                progress.advance(task)

    if not ids:
        return {"samples": 0, "elapsed_s": 0.0, "index_size_mb": 0.0}

    idx = VectorIndex()
    idx.build(ids, np.vstack(vecs))

    elapsed = time.perf_counter() - start
    from pathlib import Path as P
    index_size = P.home() / ".samplemind" / "vector_index.faiss"
    size_mb = index_size.stat().st_size / 1e6 if index_size.exists() else 0.0

    log.info("index_rebuild_complete", samples=len(ids), elapsed_s=round(elapsed, 2))
    return {"samples": len(ids), "elapsed_s": round(elapsed, 2), "index_size_mb": round(size_mb, 2)}
```

---

## 7. FastAPI Semantic Search Endpoint

```python
# src/samplemind/api/routes/semantic.py
"""
Semantic search REST endpoint.

GET  /api/v1/search/semantic?q=dark+bass&top=20&min_score=0.7
POST /api/v1/search/semantic/audio   (multipart: audio file)
POST /api/v1/index/rebuild           (admin only)

Rate-limited: 20 requests/minute per user (CLAP inference is CPU-heavy).
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query
from samplemind.core.feature_flags import is_enabled
from samplemind.api.routes.auth import get_current_active_user

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.get("/semantic")
async def text_search(
    q: str = Query(..., description="Natural language description"),
    top: int = Query(20, ge=1, le=100),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    _user=Depends(get_current_active_user),
):
    """Semantic text-to-audio search using CLAP embeddings."""
    if not is_enabled("semantic_search"):
        raise HTTPException(status_code=503, detail="Semantic search not yet available")

    from samplemind.search.embeddings import embed_text
    from samplemind.search.vector_index import get_vector_index
    from samplemind.data.repositories.sample_repository import SampleRepository

    vec = embed_text(q)
    hits = get_vector_index().search(vec, top_k=top)
    hits = [h for h in hits if h.score >= min_score]

    results = []
    for hit in hits:
        sample = SampleRepository.get_by_id(hit.sample_id)
        if sample:
            results.append({**sample.model_dump(), "similarity": round(hit.score, 4)})
    return {"query": q, "results": results, "count": len(results)}


@router.post("/semantic/audio")
async def audio_similarity_search(
    file: UploadFile,
    top: int = Query(20, ge=1, le=100),
    _user=Depends(get_current_active_user),
):
    """Find samples similar to an uploaded audio file."""
    if not is_enabled("semantic_search"):
        raise HTTPException(status_code=503, detail="Semantic search not yet available")

    import tempfile, shutil
    from pathlib import Path
    from samplemind.search.embeddings import embed_audio

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        vec = embed_audio(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    from samplemind.search.vector_index import get_vector_index
    from samplemind.data.repositories.sample_repository import SampleRepository
    hits = get_vector_index().search(vec, top_k=top)
    results = []
    for hit in hits:
        sample = SampleRepository.get_by_id(hit.sample_id)
        if sample:
            results.append({**sample.model_dump(), "similarity": round(hit.score, 4)})
    return {"results": results, "count": len(results)}
```

---

## 8. ChromaDB Alternative (Persistent Vector Store)

For users who prefer a fully managed vector DB over raw FAISS:

```python
# src/samplemind/search/chromadb_store.py
"""
ChromaDB persistent vector store — alternative to raw FAISS.

ChromaDB advantages over FAISS:
  - Built-in persistence (no manual save/load)
  - Metadata filtering alongside vector search
  - Multiple collections (one per library)
  - REST API mode for remote libraries

ChromaDB disadvantages:
  - Higher memory overhead (~2× FAISS for same dataset)
  - Slower for pure vector search (vs IndexFlatIP)
  - External dependency (starts a SQLite-backed server)

Use ChromaDB when you need hybrid search (vector + metadata filter in one query).
Use FAISS when you need maximum speed on large libraries (> 500k samples).
"""
import chromadb
from pathlib import Path
from samplemind.search.embeddings import embed_audio, embed_text

CHROMA_DIR = Path.home() / ".samplemind" / "chromadb"


def get_chroma_client() -> chromadb.Client:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(library_name: str = "default"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=f"samplemind_{library_name}",
        metadata={"hnsw:space": "cosine"},
    )


def add_sample(sample_id: int, path: str, metadata: dict,
               library: str = "default") -> None:
    """Add a sample embedding + metadata to ChromaDB."""
    collection = get_collection(library)
    vec = embed_audio(Path(path))
    collection.upsert(
        ids=[str(sample_id)],
        embeddings=[vec.tolist()],
        metadatas=[metadata],
    )


def hybrid_search(query: str, filters: dict | None = None,
                  top_k: int = 20, library: str = "default") -> list[dict]:
    """
    Hybrid search: vector similarity + metadata filtering in one query.

    Example filters:
      {"instrument": "kick"}
      {"$and": [{"energy": "high"}, {"bpm": {"$gte": 130}}]}

    Returns list of {id, distance, metadata} sorted by relevance.
    """
    collection = get_collection(library)
    vec = embed_text(query)

    kwargs = {"query_embeddings": [vec.tolist()], "n_results": top_k}
    if filters:
        kwargs["where"] = filters

    results = collection.query(**kwargs)
    return [
        {"sample_id": int(i), "score": 1.0 - d, "metadata": m}
        for i, d, m in zip(
            results["ids"][0],
            results["distances"][0],
            results["metadatas"][0],
        )
    ]
```

---

## 9. Tauri Integration — Semantic Search in Desktop App

```rust
// app/src-tauri/src/commands.rs

/// Semantic text search via Python sidecar.
/// Returns JSON array of sample results with similarity scores.
#[tauri::command]
pub async fn semantic_search(
    query: String,
    top_k: u32,
) -> Result<serde_json::Value, String> {
    use std::process::Command;
    let output = Command::new("samplemind")
        .args(["semantic", &query, "--top", &top_k.to_string(), "--json"])
        .output()
        .map_err(|e| e.to_string())?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        return Err(format!("semantic search failed: {err}"));
    }

    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
}

/// Rebuild FAISS index (background task — may take minutes for large libraries).
#[tauri::command]
pub async fn rebuild_index() -> Result<serde_json::Value, String> {
    use std::process::Command;
    let output = Command::new("samplemind")
        .args(["index", "rebuild", "--json"])
        .output()
        .map_err(|e| e.to_string())?;
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
}
```

```svelte
<!-- app/src/SemanticSearch.svelte -->
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { is_enabled } from '$lib/featureFlags';

  let query = $state('');
  let results = $state<any[]>([]);
  let loading = $state(false);

  async function search() {
    if (!query.trim()) return;
    loading = true;
    results = await invoke('semantic_search', { query, topK: 20 });
    loading = false;
  }
</script>

{#if is_enabled('semantic_search')}
<div class="semantic-search">
  <input
    bind:value={query}
    placeholder='Describe the sound: "dark atmospheric pad", "punchy trap kick"...'
    onkeydown={(e) => e.key === 'Enter' && search()}
    class="search-input"
  />
  <button onclick={search} disabled={loading}>
    {loading ? '🔍 Searching...' : '🔍 Find Similar'}
  </button>

  {#each results as r (r.id)}
  <div class="result-card">
    <span class="score">{(r.similarity * 100).toFixed(1)}%</span>
    <span class="filename">{r.filename}</span>
    <span class="instrument badge">{r.instrument}</span>
    <span class="bpm">{r.bpm} BPM</span>
  </div>
  {/each}
</div>
{/if}
```

---

## 10. Testing

```python
# tests/test_semantic_search.py
"""
Tests for Phase 11 semantic search.

The CLAP model is NOT loaded in unit tests (too slow, ~900MB download).
All CLAP calls are mocked with deterministic 512-dim random vectors.
Integration tests with real CLAP are marked @pytest.mark.slow.
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from samplemind.search.vector_index import VectorIndex


@pytest.fixture
def mock_embedding():
    """Fixed 512-dim unit vector for deterministic tests."""
    vec = np.random.default_rng(42).random(512).astype(np.float32)
    return vec / np.linalg.norm(vec)


@pytest.fixture
def small_index(mock_embedding):
    """VectorIndex with 5 pre-populated samples."""
    idx = VectorIndex()
    embeddings = np.vstack([
        np.roll(mock_embedding, i * 10) for i in range(5)
    ])
    # Renormalize after roll
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    idx.build(list(range(1, 6)), embeddings)
    return idx, mock_embedding


def test_vector_index_search_returns_top_k(small_index):
    idx, query_vec = small_index
    results = idx.search(query_vec, top_k=3)
    assert len(results) == 3
    assert results[0].score >= results[1].score >= results[2].score


def test_vector_index_scores_in_valid_range(small_index):
    idx, query_vec = small_index
    results = idx.search(query_vec, top_k=5)
    for r in results:
        assert 0.0 <= r.score <= 1.0, f"Score {r.score} out of [0, 1]"


def test_empty_index_returns_empty(mock_embedding):
    idx = VectorIndex()
    results = idx.search(mock_embedding, top_k=10)
    assert results == []


@pytest.mark.slow
def test_text_embedding_shape():
    """Requires CLAP model — only run with: uv run pytest -m slow"""
    from samplemind.search.embeddings import embed_text
    vec = embed_text("dark atmospheric pad")
    assert vec.shape == (512,)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5  # unit vector


@pytest.mark.slow
def test_audio_text_similarity_direction(kick_wav):
    """A kick drum should score higher for 'kick drum' than 'soft pad'."""
    from samplemind.search.embeddings import embed_audio, embed_text
    audio_vec  = embed_audio(kick_wav)
    kick_text  = embed_text("punchy kick drum bass")
    pad_text   = embed_text("soft atmospheric reverb pad")
    assert np.dot(audio_vec, kick_text) > np.dot(audio_vec, pad_text)
```

---

## 11. Checklist

- [ ] `uv add faiss-cpu sentence-transformers msclap` — dependencies installed
- [ ] `embed_audio()` and `embed_text()` return L2-normalized 512-dim arrays
- [ ] `VectorIndex.build()` and `search()` working
- [ ] `uv run samplemind semantic "test query"` returns results from CLI
- [ ] Feature flag `semantic_search` controls availability
- [ ] FAISS index rebuilt after every batch import
- [ ] Tauri `semantic_search` command registered in `invoke_handler!`
- [ ] Tests pass: `uv run pytest tests/test_semantic_search.py -m "not slow"`
- [ ] Slow tests pass: `uv run pytest tests/test_semantic_search.py -m slow`
- [ ] ChromaDB alternative documented (optional path)
- [ ] Index size documented in logs (`index_size_mb`)

