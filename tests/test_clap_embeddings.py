"""Tests for AudioEmbedder and CLAP vector index.

All tests run without transformers, torch, or a model download.
The mock-LLM path and the availability-check path are both covered.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ── AudioEmbedder availability ─────────────────────────────────────────────────


class TestAudioEmbedderAvailability:
    def test_is_available_false_without_transformers(self) -> None:
        with patch.dict(sys.modules, {"transformers": None, "torch": None}):
            from samplemind.ai.embeddings import AudioEmbedder

            assert not AudioEmbedder.is_available()

    def test_is_available_true_with_mocked_deps(self) -> None:
        mock_transformers = MagicMock()
        mock_torch = MagicMock()
        with patch.dict(sys.modules, {"transformers": mock_transformers, "torch": mock_torch}):
            from samplemind.ai.embeddings import AudioEmbedder

            assert AudioEmbedder.is_available()

    def test_load_raises_without_transformers(self) -> None:
        with patch.dict(sys.modules, {"transformers": None}):
            from samplemind.ai.embeddings import AudioEmbedder

            embedder = AudioEmbedder()
            with pytest.raises(RuntimeError, match="transformers"):
                embedder.load()

    def test_load_raises_without_torch(self) -> None:
        mock_transformers = MagicMock()
        with patch.dict(sys.modules, {"transformers": mock_transformers, "torch": None}):
            from samplemind.ai.embeddings import AudioEmbedder

            embedder = AudioEmbedder()
            with pytest.raises(RuntimeError, match="torch"):
                embedder.load()

    def test_not_loaded_by_default(self) -> None:
        from samplemind.ai.embeddings import AudioEmbedder

        embedder = AudioEmbedder()
        assert not embedder.is_loaded()

    def test_embed_raises_when_not_loaded(self, tmp_path: Path) -> None:
        from samplemind.ai.embeddings import AudioEmbedder

        embedder = AudioEmbedder()
        with pytest.raises(RuntimeError, match="load\\(\\)"):
            embedder.embed(tmp_path / "test.wav")

    def test_embed_text_raises_when_not_loaded(self) -> None:
        from samplemind.ai.embeddings import AudioEmbedder

        embedder = AudioEmbedder()
        with pytest.raises(RuntimeError, match="load\\(\\)"):
            embedder.embed_text("dark bass")


# ── AudioEmbedder with mocked model ───────────────────────────────────────────


class TestAudioEmbedderMocked:
    def _make_loaded_embedder(self) -> tuple:
        """Return (embedder, mock_model, mock_processor) with _model/_processor injected."""
        from samplemind.ai.embeddings import AudioEmbedder

        embedder = AudioEmbedder()
        mock_model = MagicMock()
        mock_processor = MagicMock()
        embedder._model = mock_model
        embedder._processor = mock_processor
        return embedder, mock_model, mock_processor

    def _make_mock_feature_tensor(self, vec: np.ndarray) -> MagicMock:
        """Return a mock tensor whose [0] returns a mock with .numpy() == vec."""
        inner = MagicMock()
        inner.numpy.return_value = vec
        outer = MagicMock()
        outer.__getitem__ = MagicMock(return_value=inner)
        return outer

    def _make_mock_torch(self) -> MagicMock:
        """Return a MagicMock that behaves as a usable torch module.

        Requirements:
        - torch.Tensor must be a *real class* — scipy's array_api_compat calls
          issubclass(cls, torch.Tensor) and raises TypeError if it gets a MagicMock.
        - torch.no_grad() must work as a context manager.
        """
        mock_torch = MagicMock()

        # Real class so issubclass() doesn't raise TypeError in scipy internals
        class Tensor:
            pass

        mock_torch.Tensor = Tensor
        # contextlib.nullcontext is a proper no-op context manager
        mock_torch.no_grad = contextlib.nullcontext
        return mock_torch

    def test_embed_returns_normalized_512_dim(self, tmp_path: Path) -> None:
        import soundfile as sf

        embedder, mock_model, mock_processor = self._make_loaded_embedder()
        mock_torch = self._make_mock_torch()

        # Use a real 48 kHz WAV so librosa.load works without patching
        wav_path = tmp_path / "test.wav"
        sf.write(str(wav_path), np.zeros(48_000, dtype=np.float32), 48_000)

        raw_vec = np.random.randn(512).astype(np.float32)
        mock_model.get_audio_features.return_value = self._make_mock_feature_tensor(raw_vec)
        mock_processor.return_value = {}

        with patch.dict(sys.modules, {"torch": mock_torch}):
            result = embedder.embed(wav_path)

        assert result.shape == (512,)
        assert result.dtype == np.float32
        # L2-normalised: magnitude should be ≈ 1.0
        assert abs(float(np.linalg.norm(result)) - 1.0) < 1e-5

    def test_embed_text_returns_normalized_512_dim(self) -> None:
        embedder, mock_model, mock_processor = self._make_loaded_embedder()
        mock_torch = self._make_mock_torch()

        raw_vec = np.ones(512, dtype=np.float32)
        mock_model.get_text_features.return_value = self._make_mock_feature_tensor(raw_vec)
        mock_processor.return_value = {}

        with patch.dict(sys.modules, {"torch": mock_torch}):
            result = embedder.embed_text("dark techno kick")

        assert result.shape == (512,)
        assert result.dtype == np.float32
        assert abs(float(np.linalg.norm(result)) - 1.0) < 1e-5

    def test_l2_normalize_zero_vec_does_not_crash(self) -> None:
        """_l2_normalize must return all-zeros without raising for a zero-norm vector.

        Tests the private helper directly to avoid triggering the C-extension import
        conflict that occurs when two successive librosa.load calls land inside separate
        patch.dict(sys.modules) contexts (numpy.fft._pocketfft cannot be re-loaded).
        """
        from samplemind.ai.embeddings import _l2_normalize

        zero_vec = np.zeros(512, dtype=np.float32)
        result = _l2_normalize(zero_vec)

        assert result.shape == (512,)
        assert result.dtype == np.float32
        assert float(np.linalg.norm(result)) == 0.0


# ── VectorIndex CLAP table ────────────────────────────────────────────────────


class TestVectorIndexClapTable:
    def test_ensure_tables_creates_clap_table(self, tmp_path: Path) -> None:
        from samplemind.search.vector_index import VectorIndex

        db = tmp_path / "test.db"
        with VectorIndex(db_path=db) as idx:
            idx.ensure_tables()
            rows = idx._conn.execute(
                "SELECT name FROM sqlite_master WHERE name='vec_clap_embeddings'"
            ).fetchall()
            assert len(rows) == 1

    def test_upsert_and_search_clap_returns_correct_id(self, tmp_path: Path) -> None:
        from samplemind.search.vector_index import VectorIndex

        db = tmp_path / "test.db"
        with VectorIndex(db_path=db) as idx:
            idx.ensure_tables()
            vec = np.random.rand(512).astype(np.float32)
            vec /= np.linalg.norm(vec)  # L2-normalize
            idx.upsert_clap(42, vec)
            results = idx.search_clap(vec, k=1)
            assert results == [42]

    def test_delete_removes_clap_embedding(self, tmp_path: Path) -> None:
        from samplemind.search.vector_index import VectorIndex

        db = tmp_path / "test.db"
        with VectorIndex(db_path=db) as idx:
            idx.ensure_tables()
            vec = np.random.rand(512).astype(np.float32)
            vec /= np.linalg.norm(vec)
            idx.upsert_clap(7, vec)
            idx.delete(7)
            results = idx.search_clap(vec, k=5)
            assert 7 not in results

    def test_clap_dim_constant(self) -> None:
        from samplemind.search.embeddings import CLAP_DIM

        assert CLAP_DIM == 512
