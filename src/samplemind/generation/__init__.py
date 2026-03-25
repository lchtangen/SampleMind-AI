"""Text-to-audio generation via AudioCraft (MusicGen/AudioGen) and Stable Audio.

Phase 16 — AI Generation.
Accepts a natural-language prompt and optional constraints (duration, BPM,
key, style) and returns a WAV file. The generation pipeline auto-analyzes
the output and stores it in the library. Supports multiple backends:
AudioCraft (Meta), Stable Audio Open (Stability AI), and a deterministic mock.

See: docs/en/phase-16-ai-generation.md
"""
