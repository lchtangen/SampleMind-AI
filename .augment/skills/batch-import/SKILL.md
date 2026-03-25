---
name: batch-import
description: Bulk import and analyze WAV/AIFF files from a folder with deduplication and parallel processing
---

# Skill: batch-import

Bulk import and analyze WAV/AIFF files from a folder, with deduplication, progress, and parallel processing.

## Commands

```bash
# Basic import (recursive by default)
uv run samplemind import ~/Music/Samples/

# With options
uv run samplemind import ~/Music/ --workers 8 --recursive
uv run samplemind import ~/Music/ --workers 1           # debug mode (sequential)
uv run samplemind import ~/Music/ --dry-run             # show what would be imported
uv run samplemind import ~/Music/ --json                # JSON output to stdout

# Watch mode (live folder monitoring — Phase 4 §11)
uv run samplemind watch ~/Music/Samples/ --workers 4

# Export after import
uv run samplemind import ~/Music/ && uv run samplemind export fl-studio
```

## Key Files

```
src/samplemind/cli/commands/import_cmd.py    # CLI entry point
src/samplemind/analyzer/audio_analysis.py    # analyze_file()
src/samplemind/analyzer/fingerprint.py       # fingerprint_file() — deduplication
src/samplemind/data/repositories/sample_repository.py
src/samplemind/cli/commands/watch_cmd.py     # watch mode
tests/test_import.py
```

## Import Pipeline (per file)

```
WAV/AIFF file
  │
  ▼
fingerprint_file()  →  SHA-256 of first 64KB
  │
  ├─ sha256 in DB? → SKIP (duplicate)
  │
  ▼
analyze_file()
  ├── librosa.load() → y, sr
  ├── BPM detection (beat_track)
  ├── Key detection (chromagram → Krumhansl-Schmuckler)
  ├── RMS energy → energy class (low/mid/high)
  ├── Centroid → brightness
  ├── ZCR → noisiness
  ├── LUFS loudness (Phase 2 §9)
  ├── Stereo field (Phase 2 §10)
  └── Classifier → instrument, mood, energy
  │
  ▼
SampleRepository.upsert(result)   →  INSERT OR IGNORE by sha256
  │
  ▼
(Phase 11) add_batch([id], embedding)  →  FAISS index update
```

## Performance Guide

| Workers | Use Case | Notes |
|---------|----------|-------|
| 1 | Debugging | Sequential, easy to read tracebacks |
| 4 | Default | Good balance |
| 8 | Fast NVMe, many cores | May hit librosa memory limits |
| 0 | Auto | Uses CPU count |

## Supported Formats

- `.wav` (PCM, float32, 16/24/32-bit)
- `.aiff` / `.aif`
- `.flac` (if soundfile compiled with FLAC support)
- `.mp3` (if audioread available)

## Progress Output

Rich progress bar with:
- Current file being analyzed
- Completed / total count
- Duplicates skipped count
- Errors count
- Estimated time remaining

## Testing

```bash
uv run pytest tests/test_import.py -v

# Test with synthetic fixtures
uv run pytest tests/ -k "import" -v
```

## Watch Mode (Phase 4 §11)

```bash
uv run samplemind watch ~/Music/ --recursive --workers 4
```

Events handled:
- `FILE_CREATED` → fingerprint + analyze + upsert
- `FILE_MOVED` → update path in DB
- `FILE_DELETED` → mark as missing (keeps metadata)

