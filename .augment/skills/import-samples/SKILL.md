---
name: import-samples
description: Recursively scan a folder for WAV/AIFF files, analyze each with librosa, and store in the database
---

# Skill: import-samples

Recursively scan a folder for WAV/AIFF files, analyze each with librosa,
and store results in the SQLite library database. Deduplicates by SHA-256
fingerprint. Streams progress JSON to stdout.

## When to use

Use this skill when the user asks to:
- Import a folder of samples into the library
- Bulk-analyze a sample pack
- Re-import after modifying the analyzer
- Check for duplicates in a folder before importing

## Command

```bash
uv run samplemind import "<folder>" --json
```

With explicit workers:
```bash
uv run samplemind import "<folder>" --workers 4 --json
```

Dry run (count files without writing to DB):
```bash
uv run samplemind import "<folder>" --dry-run --json
```

## Inputs

| Parameter   | Type   | Required | Default   | Description |
|-------------|--------|----------|-----------|-------------|
| folder      | path   | yes      | —         | Path to folder with WAV/AIFF files (recursive) |
| --workers   | int    | no       | 0 (auto)  | Parallel workers. 0 = cpu_count. Max useful: cpu_count. |
| --dry-run   | flag   | no       | false     | Scan and count without writing to DB |
| --json      | flag   | yes      | —         | Always pass this for machine-readable output |

## Output (JSON to stdout)

Progress events (one per file):
```json
{"current": 42, "total": 200, "file": "kick_808.wav", "status": "ok"}
```
Status values: `ok`, `duplicate`, `error`

Final summary:
```json
{"imported": 187, "duplicates": 11, "errors": 2, "elapsed_secs": 34.2, "workers_used": 8}
```

## IPC contract (important!)

- **stdout**: JSON progress events + final summary (machine-readable for Tauri)
- **stderr**: Human-readable Rich progress bar
- ⚠ Never mix human text with JSON on stdout — this breaks Tauri IPC silently

## Deduplication

Files are fingerprinted with SHA-256 of the first 64 KB:
```python
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```
If the fingerprint already exists in the library, the file is skipped silently.

## Performance guide

| Workers | Use case |
|---------|----------|
| 0 (auto) | Recommended — uses cpu_count |
| 1        | Debugging — single-threaded |
| 4        | SSD with 4+ cores |
| 8        | NVMe with 8+ cores |

Typical speed: ~5–15 files/sec per worker. CPU-bound (librosa FFT).

## Examples

```bash
# Import entire Samples folder (auto workers)
uv run samplemind import ~/Music/Samples/ --json

# Import with 4 explicit workers
uv run samplemind import ~/Music/Samples/ --workers 4 --json

# Dry run — count files first
uv run samplemind import ~/Music/Samples/ --dry-run --json

# From Rust/Tauri (parse stdout):
# Command::new("samplemind").args(["import", &path, "--json"]).output()
```

## After import

Once imported, use these to explore the library:
```bash
uv run samplemind list --json          # list all samples
uv run samplemind search --query kick  # find specific samples
uv run samplemind serve                # browse in web UI at http://localhost:5000
```

## Related skills

- `analyze-audio` — analyze a single file
- `search-library` — query results after import
- `serve` — start the web UI to browse visually

