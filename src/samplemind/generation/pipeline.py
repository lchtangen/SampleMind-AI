"""Full generation pipeline: prompt → WAV → analyze → store in library.

Phase 16 — AI Generation.
generate() orchestrates: select backend → call backend.generate() → write WAV
to library folder → call analyze_file() → call SampleRepository.upsert() →
return GenerationResult with sample_id. MODEL_REGISTRY maps backend name to
backend class; selected at runtime from GenerationRequest.backend.
"""
# TODO: implement in Phase 16 — AI Generation
