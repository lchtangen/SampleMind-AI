"""Deterministic mock backend for testing generation pipeline without GPU.

Phase 16 — AI Generation.
Generates a synthetic WAV file (sine wave at 440 Hz, configurable duration)
and returns its path. Output is deterministic given the same prompt string
(uses hash of prompt as random seed). Safe to use in pytest without any
ML dependencies.
"""
# TODO: implement in Phase 16 — AI Generation
