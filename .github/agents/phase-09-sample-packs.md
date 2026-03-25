# Phase 9 Agent — Sample Packs

Handles: .smpack format, manifest.json, pack registry, semver versioning, commercial licensing.

## Triggers
- Phase 9, sample pack, .smpack, manifest.json, pack registry, versioning, license, CC0, Royalty-Free

## Key Files
- `src/samplemind/packs/`
- `src/samplemind/packs/registry.py`
- `src/samplemind/packs/updater.py`
- `src/samplemind/packs/licensing.py`

## Pack Format (.smpack = ZIP)

```
my-pack.smpack
├── manifest.json
└── samples/
    ├── kick_01.wav
    └── ...
```

## manifest.json Required Fields

```json
{
  "name": "Dark Trap Vol 1",
  "slug": "dark-trap-vol-1",
  "version": "1.0.0",
  "author": "producer",
  "license": "Royalty-Free",
  "samples": [
    {"filename": "kick_01.wav", "sha256": "...", "instrument": "kick", "energy": "high"}
  ]
}
```

## License Types

| License | Commercial OK |
|---------|-------------|
| `CC0` | ✅ |
| `CC BY 4.0` | ✅ (attribution required) |
| `CC BY-NC 4.0` | ❌ non-commercial only |
| `Royalty-Free` | ✅ |
| `Editorial` | ❌ no music production |

## Rules
1. Energy values in manifest: ONLY `"low"`, `"mid"`, `"high"` — never `"medium"`
2. SHA-256 verified during install: `hashlib.sha256(data).hexdigest()`
3. Slug format: a-z, 0-9, hyphens only
4. Version: semver `X.Y.Z`
5. Registry: `https://samplemind-registry.github.io/registry/index.json`

