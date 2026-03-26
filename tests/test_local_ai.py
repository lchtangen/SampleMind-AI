"""Tests for LocalAIEngine — unit tests with mocked llama-cpp-python.

All tests run without llama-cpp-python or huggingface-hub installed.
The mock LLM path and the rule-based fallback path are both covered.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Rule-based tag generation ──────────────────────────────────────────────────


class TestRuleBasedTags:
    def test_kick_high_energy_aggressive(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        tags = LocalAIEngine._rule_based_tags(
            {
                "instrument": "kick",
                "bpm": 145,
                "energy": "high",
                "mood": "aggressive",
                "key": "A min",
            }
        )
        assert "kick" in tags
        # BPM 145 → drum-n-bass
        assert "drum-n-bass" in tags
        assert len(tags) <= 5

    def test_pad_low_energy_dark(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        tags = LocalAIEngine._rule_based_tags(
            {
                "instrument": "pad",
                "bpm": 75,
                "energy": "low",
                "mood": "dark",
                "key": "Dm",
            }
        )
        assert "pad" in tags
        assert "ambient" in tags  # low + dark → ambient
        assert len(tags) <= 5

    def test_house_bpm_range(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        tags = LocalAIEngine._rule_based_tags(
            {"bpm": 124, "energy": "mid", "mood": "chill"}
        )
        assert "house" in tags
        assert "chill" in tags

    def test_minor_key_detection(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        # Long form: "A min"
        tags_long = LocalAIEngine._rule_based_tags({"key": "A min"})
        assert "minor" in tags_long

        # Short form: "Am"
        tags_short = LocalAIEngine._rule_based_tags({"key": "Am"})
        assert "minor" in tags_short

    def test_major_key_does_not_get_minor_tag(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        tags = LocalAIEngine._rule_based_tags({"key": "C maj"})
        assert "minor" not in tags
        assert "major" in tags

    def test_empty_features_no_crash(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        tags = LocalAIEngine._rule_based_tags({})
        assert isinstance(tags, list)
        assert len(tags) <= 5

    def test_at_most_five_tags(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        # Provide all fields to maximise tag count
        tags = LocalAIEngine._rule_based_tags(
            {
                "instrument": "kick",
                "bpm": 145,
                "energy": "high",
                "mood": "aggressive",
                "key": "Am",
            }
        )
        assert len(tags) <= 5
        assert len(tags) == len(set(tags)), "tags must be unique"


# ── LocalAIEngine class ────────────────────────────────────────────────────────


class TestLocalAIEngine:
    def test_not_loaded_by_default(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        engine = LocalAIEngine()
        assert not engine.is_loaded()

    def test_generate_tags_falls_back_when_not_loaded(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        engine = LocalAIEngine()
        tags = engine.generate_tags({"instrument": "kick", "bpm": 128, "energy": "high"})
        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_generate_tags_with_mock_llm(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        engine = LocalAIEngine()
        mock_llm = MagicMock()
        mock_llm.create_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"tags": ["house", "kick", "120bpm", "groovy", "punchy"]}
                        )
                    }
                }
            ]
        }
        engine._llm = mock_llm  # inject mock directly

        tags = engine.generate_tags({"instrument": "kick", "bpm": 120, "energy": "high"})
        assert tags == ["house", "kick", "120bpm", "groovy", "punchy"]
        mock_llm.create_chat_completion.assert_called_once()

    def test_generate_tags_falls_back_on_llm_exception(self) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        engine = LocalAIEngine()
        mock_llm = MagicMock()
        mock_llm.create_chat_completion.side_effect = RuntimeError("CUDA OOM")
        engine._llm = mock_llm  # inject mock that raises

        # Should not raise — falls back to rule-based
        tags = engine.generate_tags({"instrument": "pad", "bpm": 90, "energy": "low"})
        assert isinstance(tags, list)

    def test_load_llm_raises_without_llama_cpp(self, tmp_path: Path) -> None:
        dummy = tmp_path / "model.gguf"
        dummy.write_bytes(b"fake-gguf-data")

        with patch.dict(sys.modules, {"llama_cpp": None}):
            from samplemind.ai.local_models import LocalAIEngine

            engine = LocalAIEngine(model_path=dummy)
            with pytest.raises(RuntimeError, match="llama-cpp-python"):
                engine.load_llm()

    def test_load_llm_raises_file_not_found(self, tmp_path: Path) -> None:
        from samplemind.ai.local_models import LocalAIEngine

        # Point at a non-existent file; llama_cpp itself isn't needed for this check
        engine = LocalAIEngine(model_path=tmp_path / "nonexistent.gguf")

        # Provide a mock llama_cpp so we get past the ImportError
        mock_llama_cpp = MagicMock()
        with patch.dict(sys.modules, {"llama_cpp": mock_llama_cpp}):
            with pytest.raises(FileNotFoundError, match="GGUF model not found"):
                engine.load_llm()

    def test_download_model_raises_without_huggingface_hub(self, tmp_path: Path) -> None:
        with patch.dict(sys.modules, {"huggingface_hub": None}):
            from samplemind.ai.local_models import LocalAIEngine

            with pytest.raises(RuntimeError, match="huggingface-hub"):
                LocalAIEngine.download_model(dest_dir=tmp_path)
