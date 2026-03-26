"""Local AI engine using llama-cpp-python for offline inference.

Phase 5 — PREMIUM_AI_EXECUTION_PLAN Task 5.1:
  Llama 3.2 1B GGUF-based auto-tagger.
  Goals: <5s model load, <500ms tag generation, zero cloud API calls.

Install the optional dependency group to enable LLM inference:
    uv sync --extra local-ai

Without it, generate_tags() falls back to fast rule-based tag generation
derived deterministically from audio analysis metadata (BPM, key, instrument,
energy, mood).  The fallback produces useful tags and never raises.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Any


class LocalAIEngine:
    """Wraps llama-cpp-python Llama for audio sample tag generation.

    Usage::

        engine = LocalAIEngine()
        try:
            engine.load_llm()          # optional — falls back to rule-based
        except (FileNotFoundError, RuntimeError):
            pass
        tags = engine.generate_tags({"bpm": 128, "instrument": "kick", ...})
    """

    DEFAULT_MODEL_FILENAME: str = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
    HF_REPO_ID: str = "bartowski/Llama-3.2-1B-Instruct-GGUF"
    DEFAULT_MODELS_DIR: Path = Path("~/.cache/samplemind/models").expanduser()

    def __init__(
        self,
        model_path: Path | None = None,
        n_ctx: int = 2048,
        n_threads: int = 4,
    ) -> None:
        self._model_path: Path = (
            model_path or self.DEFAULT_MODELS_DIR / self.DEFAULT_MODEL_FILENAME
        )
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._llm: object | None = None
        # llama_cpp.Llama is not thread-safe; serialise all inference calls.
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def load_llm(self, model_path: Path | None = None) -> None:
        """Load the GGUF model into memory.

        Args:
            model_path: Override the model file path.

        Raises:
            RuntimeError: If llama-cpp-python is not installed.
            FileNotFoundError: If the GGUF file does not exist at the resolved path.
        """
        try:
            from llama_cpp import Llama  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is required for local AI inference.  "
                "Install it with: uv sync --extra local-ai"
            ) from exc

        path = model_path or self._model_path
        if not path.exists():
            raise FileNotFoundError(
                f"GGUF model not found at {path}.  "
                "Download it with: samplemind tag --download-model"
            )

        self._llm = Llama(
            model_path=str(path),
            n_ctx=self._n_ctx,
            n_threads=self._n_threads,
            n_gpu_layers=0,  # CPU-only — safe default across all platforms
            verbose=False,
        )

    def is_loaded(self) -> bool:
        """Return True if the GGUF model is loaded and ready for inference."""
        return self._llm is not None

    def generate_tags(self, audio_features: dict[str, Any]) -> list[str]:
        """Generate up to 5 descriptive tags from audio analysis metadata.

        Uses the LLM when loaded; silently falls back to rule-based tags
        if the model is not loaded or if inference raises any exception.

        Args:
            audio_features: Dict with keys bpm, key, instrument, energy,
                            mood, rms (and any extra keys — they are ignored).

        Returns:
            List of 1-5 lowercase tag strings.
        """
        if not self.is_loaded():
            return self._rule_based_tags(audio_features)

        prompt = _build_tagging_prompt(audio_features)
        with self._lock:
            try:
                response = self._llm.create_chat_completion(  # type: ignore[attr-defined]
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=128,
                    temperature=0.1,
                )
                content: str = response["choices"][0]["message"]["content"]
                parsed: dict[str, Any] = json.loads(content)
                tags: list[str] = parsed.get("tags", [])
                if tags:
                    return [str(t).lower().strip() for t in tags[:5]]
            except Exception:  # noqa: S110 — intentional graceful degradation to rule-based
                pass

        return self._rule_based_tags(audio_features)

    # ──────────────────────────────────────────────────────────────────────────
    # Model download
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def download_model(
        cls,
        filename: str = DEFAULT_MODEL_FILENAME,
        dest_dir: Path | None = None,
    ) -> Path:
        """Download a GGUF model from HuggingFace Hub.

        Args:
            filename: GGUF filename to download from the repo.
            dest_dir: Destination directory; defaults to DEFAULT_MODELS_DIR.

        Returns:
            Local path of the downloaded model file.

        Raises:
            RuntimeError: If huggingface-hub is not installed.
        """
        try:
            from huggingface_hub import hf_hub_download  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "huggingface-hub is required to download models.  "
                "Install it with: uv sync --extra local-ai"
            ) from exc

        target = dest_dir or cls.DEFAULT_MODELS_DIR
        target.mkdir(parents=True, exist_ok=True)
        local_path: str = hf_hub_download(
            repo_id=cls.HF_REPO_ID,
            filename=filename,
            local_dir=str(target),
        )
        return Path(local_path)

    # ──────────────────────────────────────────────────────────────────────────
    # Rule-based fallback (no model required)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _rule_based_tags(features: dict[str, Any]) -> list[str]:
        """Deterministic tag generation from audio metadata — no LLM needed.

        Derives genre/style tags from BPM range, instrument, energy/mood
        combination, and key tonality.  Returns at most 5 unique tags.
        """
        tags: list[str] = []

        bpm: float = float(features.get("bpm") or 0.0)
        instrument: str = str(features.get("instrument") or "").lower()
        energy: str = str(features.get("energy") or "").lower()
        mood: str = str(features.get("mood") or "").lower()
        key: str = str(features.get("key") or "").lower()

        # 1. Instrument — always include when known
        if instrument and instrument != "unknown":
            tags.append(instrument)

        # 2. BPM → genre hint
        if bpm >= 160:
            tags.append("hardcore")
        elif bpm >= 140:
            tags.append("drum-n-bass")
        elif bpm >= 128:
            tags.append("techno")
        elif bpm >= 120:
            tags.append("house")
        elif bpm >= 100:
            tags.append("mid-tempo")
        elif bpm >= 70:
            tags.append("lo-fi")
        elif bpm > 0:
            tags.append("slow")

        # 3. Energy + mood combos
        if energy == "high" and mood == "aggressive":
            tags.append("industrial")
        elif energy == "low" and mood in ("dark", "melancholic"):
            tags.append("ambient")
        elif energy == "high" and mood == "euphoric":
            tags.append("uplifting")
        elif mood == "chill":
            tags.append("chill")
        elif mood == "dark":
            tags.append("dark")

        # 4. Key tonality
        # Matches "A min", "F# min", "Am", "Bm" — avoids false match on "major"
        if "min" in key or (len(key) >= 2 and key[-1] == "m" and key[-2].isalpha()):
            tags.append("minor")
        elif key:
            tags.append("major")

        # Deduplicate while preserving insertion order; cap at 5
        seen: set[str] = set()
        result: list[str] = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                result.append(t)
            if len(result) == 5:
                break
        return result


# ──────────────────────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────────────────────


def _build_tagging_prompt(features: dict[str, Any]) -> str:
    """Build a concise chat prompt for JSON-mode tag generation."""
    bpm = features.get("bpm", "unknown")
    key = features.get("key", "unknown")
    instrument = features.get("instrument", "unknown")
    energy = features.get("energy", "unknown")
    mood = features.get("mood", "unknown")
    rms = features.get("rms") or 0.0

    return (
        "Analyze this audio sample and generate exactly 5 descriptive genre/style tags.\n\n"
        f"BPM: {bpm}\nKey: {key}\nInstrument: {instrument}\n"
        f"Energy: {energy}\nMood: {mood}\nRMS: {float(rms):.3f}\n\n"
        'Respond with JSON only: {"tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]}'
    )
