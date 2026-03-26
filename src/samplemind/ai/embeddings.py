"""CLAP audio embeddings via HuggingFace transformers.

Phase 5 — PREMIUM_AI_EXECUTION_PLAN Task 5.2:
  512-dim semantic audio (and text) embeddings via laion/clap-htsat-unfused.
  Goals: cross-modal audio/text search, numpy 2.x compatible, CPU-safe default.

Install the optional dependency group to enable CLAP inference:
    uv sync --extra clap

Without it, AudioEmbedder.is_available() returns False and embed() raises
RuntimeError — callers should check is_available() before instantiating.

Note: laion-clap==1.1.7 is NOT used here because it requires numpy<2.0, which
conflicts with Python 3.13 + numpy>=2.2. We use transformers.ClapModel instead,
which is numpy 2.x compatible.
"""

from __future__ import annotations

from pathlib import Path
import threading

import numpy as np


class AudioEmbedder:
    """Wraps transformers.ClapModel for 512-dim audio and text embeddings.

    Usage::

        embedder = AudioEmbedder()
        embedder.load()                          # lazy — ~630 MB on first run
        vec = embedder.embed(Path("kick.wav"))   # shape (512,), float32, L2-normalized
        tvec = embedder.embed_text("dark pad")   # same 512-dim space — cross-modal search
    """

    DIM: int = 512
    MODEL_NAME: str = "laion/clap-htsat-unfused"
    SAMPLE_RATE: int = 48_000  # CLAP requires 48 kHz input

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: object | None = None
        self._processor: object | None = None
        # ClapModel is not thread-safe for concurrent inference — serialise all calls
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load ClapModel + ClapProcessor into memory.

        Raises:
            RuntimeError: If transformers or torch are not installed.
        """
        try:
            from transformers import (  # type: ignore[import-untyped]
                ClapModel,
                ClapProcessor,
            )
        except ImportError as exc:
            raise RuntimeError(
                "transformers is required for CLAP audio embeddings. "
                "Install with: uv sync --extra clap"
            ) from exc
        try:
            import torch  # type: ignore[import-untyped]  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "torch is required for CLAP audio embeddings. "
                "Install with: uv sync --extra clap"
            ) from exc

        with self._lock:
            self._model = ClapModel.from_pretrained(self._model_name)
            self._processor = ClapProcessor.from_pretrained(self._model_name)

    def is_loaded(self) -> bool:
        """Return True if the model is loaded and ready."""
        return self._model is not None

    def embed(self, path: Path) -> np.ndarray:
        """Return a 512-dim float32 embedding for an audio file.

        The embedding is L2-normalized so cosine similarity equals dot product.
        This allows sqlite-vec's Euclidean KNN to produce cosine-equivalent ranking.

        Args:
            path: Path to a WAV or AIFF audio file.

        Returns:
            float32 ndarray of shape (512,).

        Raises:
            RuntimeError: If the model is not loaded.
        """
        if not self.is_loaded():
            raise RuntimeError(
                "AudioEmbedder is not loaded. Call load() first."
            )

        import librosa
        import torch  # type: ignore[import-untyped]

        audio, _ = librosa.load(str(path), sr=self.SAMPLE_RATE, mono=True)

        with self._lock:
            inputs = self._processor(  # type: ignore[call-arg]
                audios=audio,
                sampling_rate=self.SAMPLE_RATE,
                return_tensors="pt",
            )
            with torch.no_grad():
                features = self._model.get_audio_features(**inputs)  # type: ignore[union-attr]

        vec: np.ndarray = features[0].numpy().astype(np.float32)
        return _l2_normalize(vec)

    def embed_text(self, query: str) -> np.ndarray:
        """Return a 512-dim float32 embedding for a text query (cross-modal search).

        CLAP's audio and text encoders share the same projection space, so the
        returned vector is directly comparable to embed() output via KNN search.

        Args:
            query: Natural-language description, e.g. "dark ambient pad in A minor".

        Returns:
            float32 ndarray of shape (512,).

        Raises:
            RuntimeError: If the model is not loaded.
        """
        if not self.is_loaded():
            raise RuntimeError(
                "AudioEmbedder is not loaded. Call load() first."
            )

        import torch  # type: ignore[import-untyped]

        with self._lock:
            inputs = self._processor(  # type: ignore[call-arg]
                text=[query],
                return_tensors="pt",
                padding=True,
            )
            with torch.no_grad():
                features = self._model.get_text_features(**inputs)  # type: ignore[union-attr]

        vec: np.ndarray = features[0].numpy().astype(np.float32)
        return _l2_normalize(vec)

    @classmethod
    def is_available(cls) -> bool:
        """Return True if transformers and torch are importable (no model download)."""
        try:
            import torch  # type: ignore[import-untyped]  # noqa: F401
            import transformers  # type: ignore[import-untyped]  # noqa: F401

            return True
        except ImportError:
            return False


# ── Private helpers ───────────────────────────────────────────────────────────


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    """Return a unit-norm copy of vec; returns vec unchanged if norm is zero."""
    norm = float(np.linalg.norm(vec))
    if norm > 0.0:
        return (vec / norm).astype(np.float32)
    return vec.astype(np.float32)
