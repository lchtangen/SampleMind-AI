"""Sample pack (.smpack) creation, import, and verification.

Phase 9 — Sample Packs.
A .smpack file is a ZIP archive containing:
  - manifest.json  (metadata: name, version, author, description, checksums)
  - *.wav files    (the actual audio samples)
  - LICENSE        (optional license text)

The manifest is SHA-256 signed to prevent tampering. Checksums are verified
on import before the pack is added to the library.

See: docs/en/phase-09-sample-packs.md
"""
