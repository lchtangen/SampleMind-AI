"""Audio and text embedding generation for semantic search.

Phase 11 — Semantic Search.

Audio: 10-dimensional float32 feature vector derived from analyze_file()
output. Deterministic, zero model download, works on Python 3.13 + numpy>=2.

Text: 384-dimensional sentence-transformers embedding (all-MiniLM-L6-v2).
Requires: uv sync --extra embeddings. Lazily imported so the core package
starts up instantly even without the model installed.

Public API:
  embed_audio(path: Path) -> np.ndarray  # shape (10,) float32
  embed_text(query: str)  -> np.ndarray  # shape (384,) float32
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

AUDIO_DIM: int = 10
TEXT_DIM: int = 384

# Lookup tables for categorical → numeric mapping
_ENERGY_MAP = {"low": 0, "mid": 1, "high": 2}
_MOOD_MAP = {
    "dark": 0,
    "chill": 1,
    "neutral": 2,
    "melancholic": 3,
    "euphoric": 4,
    "aggressive": 5,
}
_INSTRUMENT_MAP = {
    "unknown": 0,
    "loop": 1,
    "hihat": 2,
    "snare": 3,
    "kick": 4,
    "bass": 5,
    "pad": 6,
    "lead": 7,
    "sfx": 8,
}
_NOTE_MAP = {
    "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
    "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
}


def _parse_key_index(key: str | None) -> float:
    """Return normalized key index in [0, 1] from a key string like 'C# min'."""
    if not key:
        return 0.0
    root = key.split()[0] if " " in key else key
    idx = _NOTE_MAP.get(root, 0)
    return float(idx) / 11.0


def embed_audio(path: Path) -> np.ndarray:
    """Return a 10-dimensional float32 feature vector for an audio file.

    Derived from analyze_file() output; values normalized to approximate [0, 1].
    The vector layout is:
      [0] bpm / 300
      [1] key_index / 11
      [2] energy_int / 2
      [3] mood_int / 5
      [4] instrument_int / 8
      [5] rms (log-normalized)
      [6] centroid_norm
      [7] zcr (log-normalized)
      [8] 0.0  (reserved for future features)
      [9] 0.0  (reserved for future features)

    Args:
        path: Path to the WAV or AIFF file to embed.

    Returns:
        float32 ndarray of shape (10,).
    """
    from samplemind.analyzer.audio_analysis import analyze_file  # noqa: PLC0415
    import librosa  # noqa: PLC0415

    features = analyze_file(str(path))

    # Reload audio for low-level features (rms, centroid, zcr)
    y, sr = librosa.load(str(path), sr=22050)
    rms = float(np.sqrt(np.mean(y ** 2)))
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    centroid_norm = float(centroid.mean()) / (sr / 2)
    zcr = float(librosa.feature.zero_crossing_rate(y).mean())

    bpm_norm = float(features["bpm"]) / 300.0
    key_norm = _parse_key_index(features.get("key"))
    energy_norm = float(_ENERGY_MAP.get(features.get("energy", ""), 0)) / 2.0
    mood_norm = float(_MOOD_MAP.get(features.get("mood", ""), 0)) / 5.0
    instrument_norm = float(_INSTRUMENT_MAP.get(features.get("instrument", ""), 0)) / 8.0

    # Log-normalize rms and zcr (values are small floats — log scale spreads them)
    rms_log = float(np.log1p(rms * 100) / np.log1p(100))
    zcr_log = float(np.log1p(zcr * 1000) / np.log1p(1000))

    vec = np.array(
        [bpm_norm, key_norm, energy_norm, mood_norm, instrument_norm,
         rms_log, centroid_norm, zcr_log, 0.0, 0.0],
        dtype=np.float32,
    )
    return vec


def embed_text(query: str) -> np.ndarray:
    """Return a 384-dimensional text embedding via sentence-transformers.

    Model: all-MiniLM-L6-v2 (lazy-loaded on first call, ~22 MB).
    Requires: uv sync --extra embeddings

    Args:
        query: Natural language description of a sample sound.

    Returns:
        float32 ndarray of shape (384,).

    Raises:
        RuntimeError: If sentence-transformers is not installed.
    """
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is required for text embedding. "
            "Install with: uv sync --extra embeddings"
        ) from exc

    model = _get_text_model()
    embedding = model.encode(query, convert_to_numpy=True)
    return np.asarray(embedding, dtype=np.float32)


# ── Lazy model cache ──────────────────────────────────────────────────────────

_text_model: object | None = None


def _get_text_model() -> object:
    """Return cached SentenceTransformer model, loading on first call."""
    global _text_model  # noqa: PLW0603
    if _text_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        _text_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _text_model
