"""Full generation pipeline: prompt → WAV → analyze → store in library.

Phase 16 — AI Generation.
generate() orchestrates: select backend → call backend.generate() → write WAV
to library folder → call analyze_file() → call SampleRepository.upsert() →
return GenerationResult with sample_id. MODEL_REGISTRY maps backend name to
backend class; selected at runtime from GenerationRequest.backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from samplemind.generation.backends.audiocraft_backend import AudioCraftBackend
from samplemind.generation.backends.mock_backend import MockBackend
from samplemind.generation.backends.stable_audio_backend import StableAudioBackend
from samplemind.generation.models import GenerationRequest, GenerationResult

if TYPE_CHECKING:
    pass

# Registry: backend name → class.  New backends register here.
MODEL_REGISTRY: dict[str, type] = {
    "mock": MockBackend,
    "audiocraft": AudioCraftBackend,
    "stable_audio": StableAudioBackend,
}


def _default_dest() -> Path:
    """Return the default output directory for generated samples."""
    from samplemind.core.config import get_settings

    settings = get_settings()
    # Derive a sibling directory next to the DB file
    db_path = Path(str(settings.database_url).removeprefix("sqlite:///"))
    dest = db_path.parent / "generated"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def generate(
    req: GenerationRequest,
    dest_dir: Path | None = None,
    auto_import: bool = False,
) -> GenerationResult:
    """Run the full generation pipeline for *req*.

    Args:
        req: Parameters for the generation call.
        dest_dir: Directory to write the WAV file.  Defaults to
            ``~/.samplemind/generated/`` (resolved via ``get_settings()``).
        auto_import: If ``True``, analyze the output and upsert it into the
            sample library.  ``GenerationResult.sample_id`` will be set.

    Returns:
        A :class:`GenerationResult` populated with path, duration, and
        (if ``auto_import=True``) detected audio features and ``sample_id``.

    Raises:
        ValueError: If ``req.backend`` is not in :data:`MODEL_REGISTRY`.
    """
    backend_cls = MODEL_REGISTRY.get(req.backend)
    if backend_cls is None:
        available = list(MODEL_REGISTRY)
        raise ValueError(
            f"Unknown backend: {req.backend!r}. Choose from: {available}"
        )

    backend = backend_cls()
    out_path = backend.generate(req, dest_dir or _default_dest())

    # Build initial result (features populated below if auto_import)
    result = GenerationResult(
        output_path=out_path,
        duration_seconds=req.duration_seconds,
        backend_used=req.backend,
    )

    if auto_import:
        _auto_import(result, out_path)

    return result


def _auto_import(result: GenerationResult, out_path: Path) -> None:
    """Analyze *out_path* and upsert into the sample library.

    Populates ``result.bpm_detected``, ``result.key_detected``,
    ``result.instrument_detected``, ``result.energy_detected``, and
    ``result.sample_id`` in-place.
    """
    from samplemind.analyzer.audio_analysis import analyze_file
    from samplemind.core.models.sample import SampleCreate
    from samplemind.data.orm import init_orm
    from samplemind.data.repositories.sample_repository import SampleRepository

    init_orm()

    features = analyze_file(str(out_path))

    result.bpm_detected = features.get("bpm")
    result.key_detected = features.get("key")
    result.instrument_detected = features.get("instrument")
    result.energy_detected = features.get("energy")

    sample = SampleRepository.upsert(
        SampleCreate(
            filename=out_path.name,
            path=str(out_path.resolve()),
            bpm=result.bpm_detected,
            key=result.key_detected,
            instrument=result.instrument_detected,
            energy=result.energy_detected,
        )
    )
    result.sample_id = sample.id
