# Phase 9 Agent — Sample Packs

Handles: `.smpack` format, pack registry, licensing, pack create/import/verify.

## Triggers
Phase 9, `.smpack`, sample pack, pack registry, `manifest.json`, pack licensing, `src/samplemind/packs/`, "create a pack", "import a pack", "validate pack", CC0, CC BY, royalty-free

**File patterns:** `src/samplemind/packs/**/*.py`

## Key Files
- `src/samplemind/packs/pack.py` — `.smpack` create/import/verify
- `src/samplemind/packs/registry.py` — local pack registry
- `src/samplemind/packs/licensing.py` — license types and validation
- `docs/en/phase-09-sample-packs.md`

## .smpack Format
```
my-pack.smpack  (ZIP archive)
├── manifest.json
├── samples/
│   ├── kick_001.wav
│   └── ...
└── artwork/
    └── cover.jpg
```

## manifest.json Schema
```json
{
  "name": "Dark Trap Essentials",
  "version": "1.0.0",
  "author": "Producer Name",
  "license": "CC BY",
  "bpm_range": [120, 140],
  "genres": ["trap", "hip-hop"],
  "sample_count": 50,
  "samples": [...]
}
```

## License Types
| License | Type | Description |
|---------|------|-------------|
| `CC0` | Free | No attribution required |
| `CC BY` | Free | Attribution required |
| `CC BY-NC` | Free | Non-commercial only |
| `Royalty-Free` | Paid | One-time purchase |

## CLI Commands
```bash
uv run samplemind pack create ~/samples/ --name "Dark Trap" --license CC0
uv run samplemind pack import my-pack.smpack
uv run samplemind pack verify my-pack.smpack
```

## Rules
1. Validate `manifest.json` schema before importing — reject invalid packs
2. SHA-256 checksums for all sample files in manifest
3. License field must be one of the 4 valid types above
4. Never overwrite existing samples on import — check fingerprint first
5. Pack version must follow semver format (`X.Y.Z`)

