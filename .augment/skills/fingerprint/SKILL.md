# Skill: fingerprint

SHA-256 audio fingerprinting for deduplication — identify identical files regardless of filename.

## Commands

```bash
# Fingerprint a single file
uv run samplemind fingerprint ~/Music/kick.wav

# Find duplicates in current library
uv run samplemind duplicates --json

# Find duplicates before import (dry-run)
uv run samplemind import ~/Music/ --dedupe --dry-run

# Show all samples with the same fingerprint
uv run samplemind duplicates --group --json
```

## Implementation

```python
# src/samplemind/analyzer/fingerprint.py
import hashlib
from pathlib import Path

def fingerprint_file(path: Path) -> str:
    """
    SHA-256 of first 64 KB of the audio file.
    Fast enough for real-time use (< 1ms for most files).
    NOT sensitive to metadata changes — only audio data.
    Matches the sync deduplication in Phase 13 cloud sync.
    """
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

## Key Facts

- **Algorithm:** SHA-256 of first 64 KB (65,536 bytes)
- **Speed:** < 1ms per file on NVMe, ~5ms on HDD
- **Collision probability:** Negligible (SHA-256 is collision-resistant)
- **Not sensitive to:** filename, path, metadata tags
- **Sensitive to:** any change in audio content
- **Cloud sync:** same algorithm used in Phase 13 for R2 deduplication
- **DB column:** `samples.sha256` (TEXT, UNIQUE)

## Key Files

```
src/samplemind/analyzer/fingerprint.py  # fingerprint_file()
src/samplemind/data/repositories/sample_repository.py  # upsert by sha256
tests/test_fingerprint.py
```

## Database Deduplication

```sql
-- Upsert by SHA-256 (never creates duplicates)
INSERT OR IGNORE INTO samples (sha256, filename, path, ...)
VALUES (?, ?, ?, ...);
```

## Testing

```bash
uv run pytest tests/test_fingerprint.py -v

# Verify deduplication:
cp tests/fixtures/kick.wav /tmp/kick_copy.wav
uv run samplemind fingerprint tests/fixtures/kick.wav
uv run samplemind fingerprint /tmp/kick_copy.wav
# Both should return the same SHA-256
```

## Integration Points

- **Import pipeline:** `fingerprint_file()` called before inserting to DB
- **Cloud sync (Phase 13):** S3 key includes SHA-256 for dedup: `audio/{sha256[:2]}/{sha256}.wav`
- **Watch mode (Phase 4 §11):** Fingerprint checked before re-importing on FILE_CREATED events
- **Batch import:** Skip import if SHA-256 already in `samples.sha256`

