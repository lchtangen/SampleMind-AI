"""Tests for Phase 16 AI Generation.

All tests use MockBackend — no GPU, no audiocraft, no ML dependencies required.
Tests cover the Pydantic models, MockBackend behaviour, the pipeline, and the
MODEL_REGISTRY sentinel check.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import soundfile as sf

from samplemind.generation.backends.mock_backend import MockBackend
from samplemind.generation.models import GenerationRequest, GenerationResult
from samplemind.generation.pipeline import MODEL_REGISTRY, generate

# ── GenerationRequest / GenerationResult defaults ─────────────────────────────


def test_generation_request_defaults() -> None:
    """Pydantic defaults are applied correctly without explicit values."""
    req = GenerationRequest(prompt="test kick")
    assert req.duration_seconds == 5.0
    assert req.backend == "mock"
    assert req.bpm is None
    assert req.key is None
    assert req.instrument is None
    assert req.seed is None
    assert req.guidance_scale == 3.0


def test_generation_request_validation_rejects_zero_duration() -> None:
    """duration_seconds must be > 0."""
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        GenerationRequest(prompt="x", duration_seconds=0)


def test_generation_request_validation_rejects_over_60() -> None:
    """duration_seconds must be ≤ 60."""
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        GenerationRequest(prompt="x", duration_seconds=61)


# ── MockBackend.generate ───────────────────────────────────────────────────────


def test_mock_backend_creates_wav(tmp_path: Path) -> None:
    """generate() creates a .wav file in dest_dir."""
    req = GenerationRequest(prompt="dark trap kick", backend="mock")
    backend = MockBackend()
    out = backend.generate(req, tmp_path)

    assert out.exists()
    assert out.suffix == ".wav"
    assert out.parent == tmp_path


def test_mock_backend_is_deterministic(tmp_path: Path) -> None:
    """Same prompt → same WAV content (identical bytes)."""
    req = GenerationRequest(prompt="hi hat roll 16th", backend="mock")
    backend = MockBackend()

    out1 = backend.generate(req, tmp_path / "a")
    out2 = backend.generate(req, tmp_path / "b")

    assert out1.read_bytes() == out2.read_bytes()


def test_mock_backend_duration_approx(tmp_path: Path) -> None:
    """Generated WAV has approximately the requested duration (±5%)."""
    req = GenerationRequest(prompt="pad chord", duration_seconds=5.0, backend="mock")
    backend = MockBackend()
    out = backend.generate(req, tmp_path)

    data, sr = sf.read(str(out))
    actual_duration = len(data) / sr
    assert abs(actual_duration - req.duration_seconds) < req.duration_seconds * 0.05


def test_mock_backend_seed_override(tmp_path: Path) -> None:
    """Explicit req.seed overrides the prompt-derived seed."""
    req_a = GenerationRequest(prompt="aaaa", seed=42, backend="mock")
    req_b = GenerationRequest(prompt="bbbb", seed=42, backend="mock")
    backend = MockBackend()

    out_a = backend.generate(req_a, tmp_path / "a")
    out_b = backend.generate(req_b, tmp_path / "b")

    # Different prompts but same seed → same WAV
    assert out_a.read_bytes() == out_b.read_bytes()


def test_mock_backend_prompt_seed_matches_hashlib(tmp_path: Path) -> None:
    """The prompt-derived seed matches the expected MD5-based value."""
    prompt = "snare crack"
    expected_seed = int(
        hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()[:8],
        16,
    )
    req = GenerationRequest(prompt=prompt, backend="mock")
    backend = MockBackend()
    out = backend.generate(req, tmp_path)

    # Filename embeds the seed
    assert str(expected_seed) in out.name


# ── pipeline.generate ─────────────────────────────────────────────────────────


def test_generate_mock_returns_result(tmp_path: Path) -> None:
    """pipeline.generate() with mock backend returns a valid GenerationResult."""
    req = GenerationRequest(prompt="bass line groove", backend="mock")
    result = generate(req, dest_dir=tmp_path)

    assert isinstance(result, GenerationResult)
    assert result.output_path.exists()
    assert result.backend_used == "mock"
    assert result.duration_seconds == req.duration_seconds
    assert result.sample_id is None  # auto_import=False by default


def test_generate_auto_import_sets_sample_id(tmp_path: Path) -> None:
    """auto_import=True runs analysis and upserts; result.sample_id is set."""
    req = GenerationRequest(prompt="808 kick", backend="mock", duration_seconds=2.0)

    # Stub out the heavy bits so the test stays fast and isolated
    mock_sample = MagicMock()
    mock_sample.id = 99

    with (
        patch("samplemind.data.orm.init_orm"),
        patch(
            "samplemind.analyzer.audio_analysis.analyze_file",
            return_value={"bpm": 128.0, "key": "C major", "instrument": "kick", "energy": "high"},
        ),
        patch(
            "samplemind.data.repositories.sample_repository.SampleRepository.upsert",
            return_value=mock_sample,
        ),
    ):
        result = generate(req, dest_dir=tmp_path, auto_import=True)

    assert result.sample_id == 99
    assert result.bpm_detected == 128.0
    assert result.instrument_detected == "kick"


def test_generate_unknown_backend_raises() -> None:
    """ValueError is raised for an unrecognised backend name."""
    req = GenerationRequest(prompt="test", backend="nonexistent_backend")
    with pytest.raises(ValueError, match="Unknown backend"):
        generate(req)


# ── MODEL_REGISTRY ────────────────────────────────────────────────────────────


def test_model_registry_contains_backends() -> None:
    """MODEL_REGISTRY has entries for all three Phase 16 backends."""
    assert "mock" in MODEL_REGISTRY
    assert "audiocraft" in MODEL_REGISTRY
    assert "stable_audio" in MODEL_REGISTRY


def test_model_registry_mock_class() -> None:
    """MODEL_REGISTRY['mock'] resolves to MockBackend."""
    assert MODEL_REGISTRY["mock"] is MockBackend
