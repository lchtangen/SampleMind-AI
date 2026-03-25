"""Generation backend registry: AudioCraft, Stable Audio, and Mock.

Phase 16 — AI Generation.
Each backend implements the BaseGenerationBackend protocol:
  generate(request: GenerationRequest) -> Path

Backends are selected at runtime by GenerationRequest.backend name.
"""
# TODO: implement in Phase 16 — AI Generation
