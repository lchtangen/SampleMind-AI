"""
samplemind.analyzer — Audio feature extraction and classification package.

Public modules:
  audio_analysis  — Full pipeline: analyze_file() returns bpm/key/energy/mood/instrument
  classifier      — Individual classifiers: classify_energy(), classify_mood(), classify_instrument()
  fingerprint     — SHA-256 deduplication: fingerprint_file(), find_duplicates()
"""

from samplemind.analyzer import audio_analysis, classifier, fingerprint

__all__ = ["audio_analysis", "classifier", "fingerprint"]
