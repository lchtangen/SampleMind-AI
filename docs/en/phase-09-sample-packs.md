# Phase 9 — Sample Packs (.smpack)

> Build a portable pack format for exporting, sharing, and importing curated sample libraries as a single file.

---

## Prerequisites

- Phases 1–8 complete
- `uv`, `pyproject.toml`, SQLModel, and Typer are configured
- Basic understanding of ZIP files and JSON

---

## Goal State

- `.smpack` format defined (ZIP containing `manifest.json` + `samples/`)
- `PackManifest` Pydantic model with versioning and SHA-256 checksums
- CLI commands: `samplemind pack create|export|import|list|verify`
- Idempotent import (duplicates skipped automatically)
- GitHub Releases distribution via the `gh` CLI

---

## 1. Pack Format

A `.smpack` file is a ZIP archive with this structure:

```
my-pack.smpack          ← ZIP file with renamed extension
├── manifest.json       ← Metadata and sample list
└── samples/
    ├── kick_128bpm_Cmin.wav
    ├── snare_trap_96bpm.wav
    └── bass_Fmaj.wav
```

### manifest.json — example

```json
{
  "name": "Trap Essentials Vol. 1",
  "slug": "trap-essentials-v1",
  "version": "1.0.0",
  "format_version": "1",
  "author": "SampleMind",
  "description": "808 bass, drums and atmospheres for trap production.",
  "bpm_range": [120, 160],
  "keys": ["C min", "F min", "A min"],
  "tags": ["trap", "808", "drums"],
  "created_at": "2025-10-01T12:00:00Z",
  "samples": [
    {
      "filename": "kick_128bpm_Cmin.wav",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "bpm": 128.0,
      "key": "C min",
      "instrument": "kick",
      "mood": "dark",
      "energy": "high",
      "duration": 0.45
    }
  ]
}
```

---

## 2. PackManifest — Pydantic Model

```python
# filename: src/samplemind/packs/manifest.py

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class SampleEntry(BaseModel):
    """Metadata for one sample inside a pack."""
    filename: str
    sha256: str                          # SHA-256 of the WAV file
    bpm: Optional[float] = None
    key: Optional[str] = None
    instrument: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    duration: Optional[float] = None


class PackManifest(BaseModel):
    """
    Top-level model for a .smpack manifest.
    format_version = "1" — bump if the JSON structure changes.
    """
    name: str
    slug: str                            # URL-friendly identifier: "trap-essentials-v1"
    version: str = "1.0.0"              # Semver for pack content
    format_version: str = "1"           # Semver for the format itself
    author: str = "Unknown"
    description: str = ""
    bpm_range: tuple[int, int] = (0, 300)
    keys: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    samples: list[SampleEntry] = Field(default_factory=list)


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash for a file (used for integrity verification on import)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
```

---

## 3. Exporting a Pack

```python
# filename: src/samplemind/packs/exporter.py

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.packs.manifest import PackManifest, SampleEntry, compute_sha256


def export_pack(
    name: str,
    slug: str,
    output_path: Path,
    *,
    instrument: Optional[str] = None,
    mood: Optional[str] = None,
    energy: Optional[str] = None,
    tags: Optional[list[str]] = None,
    author: str = "Unknown",
    description: str = "",
    version: str = "1.0.0",
) -> PackManifest:
    """
    Filter the library and export the result as a .smpack file.

    Returns the PackManifest object (with SHA-256 checksums populated).
    """
    # SampleRepository.search() is a static method — no instance needed.
    # All filter parameters are optional; omitting one means "any value".
    samples = SampleRepository.search(
        instrument=instrument,
        mood=mood,
        energy=energy,
        tags=tags,
    )

    if not samples:
        raise ValueError("No samples matched the filter — pack would be empty.")

    entries: list[SampleEntry] = []
    bpm_values: list[float] = []

    # Build the ZIP archive
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for sample in samples:
            src = Path(sample.path)
            if not src.exists():
                continue

            # Compute SHA-256 for later integrity checking
            sha = compute_sha256(src)
            dest_name = f"samples/{src.name}"
            zf.write(src, dest_name)

            entries.append(SampleEntry(
                filename=src.name,
                sha256=sha,
                bpm=sample.bpm,
                key=sample.key,
                instrument=sample.instrument,
                mood=sample.mood,
                energy=sample.energy,
                duration=sample.duration,
            ))

            if sample.bpm:
                bpm_values.append(sample.bpm)

        # Build the manifest
        manifest = PackManifest(
            name=name,
            slug=slug,
            version=version,
            author=author,
            description=description,
            bpm_range=(
                (int(min(bpm_values)), int(max(bpm_values)))
                if bpm_values else (0, 300)
            ),
            created_at=datetime.now(timezone.utc),
            samples=entries,
        )

        # Write manifest.json into the ZIP
        manifest_json = manifest.model_dump_json(indent=2)
        zf.writestr("manifest.json", manifest_json)

    return manifest
```

---

## 4. Importing a Pack

```python
# filename: src/samplemind/packs/importer.py

import hashlib
import json
import zipfile
from pathlib import Path

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.packs.manifest import PackManifest, compute_sha256


class PackImportError(Exception):
    """Raised on validation errors during pack import."""


def import_pack(
    pack_path: Path,
    dest_dir: Path,
    *,
    verify_checksums: bool = True,
    skip_analysis: bool = False,
) -> dict[str, int]:
    """
    Import a .smpack file into the library.

    - Validates the manifest format and SHA-256 checksums
    - Extracts WAV files to dest_dir
    - Analyzes and upserts each sample into the database
    - Idempotent: importing the same pack twice skips duplicates (upsert on path)

    Returns: {"imported": N, "skipped": M, "errors": K}
    """
    if not pack_path.exists():
        raise PackImportError(f"Pack file not found: {pack_path}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(pack_path, "r") as zf:
        # Read the manifest
        try:
            manifest_bytes = zf.read("manifest.json")
        except KeyError:
            raise PackImportError("Invalid pack: manifest.json is missing")

        manifest = PackManifest.model_validate_json(manifest_bytes)

        # Validate format version
        if manifest.format_version != "1":
            raise PackImportError(
                f"Unknown format version: {manifest.format_version} "
                f"(this version of SampleMind only supports v1)"
            )

        imported = skipped = errors = 0

        for entry in manifest.samples:
            src_name = f"samples/{entry.filename}"
            dest_path = dest_dir / entry.filename

            # Check if the sample already exists in the DB (idempotency check).
            # SampleRepository.get_by_name() is a static method on the repository.
            existing = SampleRepository.get_by_name(entry.filename)
            if existing and dest_path.exists():
                skipped += 1
                continue

            # Extract the WAV file
            try:
                zf.extract(src_name, dest_dir.parent)
            except KeyError:
                errors += 1
                continue

            # Verify the SHA-256 checksum
            if verify_checksums:
                actual_sha = compute_sha256(dest_path)
                if actual_sha != entry.sha256:
                    dest_path.unlink(missing_ok=True)
                    errors += 1
                    continue

            # Analyze the audio file (or use manifest metadata)
            if skip_analysis:
                metadata = {
                    "bpm": entry.bpm,
                    "key": entry.key,
                    "instrument": entry.instrument,
                    "mood": entry.mood,
                    "energy": entry.energy,
                    "duration": entry.duration,
                }
            else:
                try:
                    metadata = analyze_file(str(dest_path))
                except Exception:
                    # Fall back to manifest metadata if analysis fails
                    metadata = {
                        "bpm": entry.bpm,
                        "key": entry.key,
                        "instrument": entry.instrument,
                        "mood": entry.mood,
                        "energy": entry.energy,
                    }

            SampleRepository.upsert(str(dest_path), **metadata)
            imported += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}
```

---

## 5. CLI Commands

```python
# filename: src/samplemind/cli/commands/pack.py

import typer
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from samplemind.packs.exporter import export_pack
from samplemind.packs.importer import import_pack, PackImportError
from samplemind.packs.manifest import PackManifest

console = Console()
pack_app = typer.Typer(help="Manage .smpack sample packs.")


@pack_app.command("create")
def pack_create(
    name: str = typer.Argument(..., help="Pack display name"),
    slug: str = typer.Argument(..., help="URL-friendly ID: trap-essentials-v1"),
    output: Path = typer.Option(Path("."), "--output", "-o", help="Output folder for .smpack"),
    instrument: str = typer.Option(None, "--instrument"),
    mood: str = typer.Option(None, "--mood"),
    energy: str = typer.Option(None, "--energy"),
    author: str = typer.Option("Unknown", "--author"),
    description: str = typer.Option("", "--desc"),
    version: str = typer.Option("1.0.0", "--version"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Export a filtered set of samples as a .smpack file."""
    output.mkdir(parents=True, exist_ok=True)
    pack_path = output / f"{slug}.smpack"

    try:
        manifest = export_pack(
            name=name,
            slug=slug,
            output_path=pack_path,
            instrument=instrument,
            mood=mood,
            energy=energy,
            author=author,
            description=description,
            version=version,
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise typer.Exit(1)

    result = {
        "pack_path": str(pack_path),
        "sample_count": len(manifest.samples),
        "slug": manifest.slug,
        "version": manifest.version,
    }

    if as_json:
        print(json.dumps(result))
    else:
        console.print(f"[green]Pack created:[/green] {pack_path}")
        console.print(f"  Samples: {len(manifest.samples)}")
        console.print(f"  Version: {manifest.version}")


@pack_app.command("import")
def pack_import(
    pack_path: Path = typer.Argument(..., help="Path to the .smpack file"),
    dest: Path = typer.Option(
        Path.home() / "Music" / "SampleMind" / "imported",
        "--dest", "-d",
        help="Destination folder for extracted WAV files",
    ),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip SHA-256 verification"),
    skip_analysis: bool = typer.Option(False, "--skip-analysis", help="Use manifest metadata instead of re-analyzing"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Import a .smpack file into the library."""
    try:
        result = import_pack(
            pack_path,
            dest,
            verify_checksums=not no_verify,
            skip_analysis=skip_analysis,
        )
    except PackImportError as e:
        console.print(f"[red]Import error:[/red] {e}", err=True)
        raise typer.Exit(1)

    if as_json:
        print(json.dumps(result))
    else:
        console.print(f"[green]Import complete:[/green]")
        console.print(f"  Imported:           {result['imported']}")
        console.print(f"  Skipped (existing): {result['skipped']}")
        console.print(f"  Errors:             {result['errors']}")


@pack_app.command("verify")
def pack_verify(
    pack_path: Path = typer.Argument(..., help="Path to the .smpack file"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Validate a .smpack file without importing it."""
    import zipfile

    issues: list[str] = []

    if not pack_path.exists():
        console.print(f"[red]File not found:[/red] {pack_path}", err=True)
        raise typer.Exit(1)

    try:
        with zipfile.ZipFile(pack_path, "r") as zf:
            names = zf.namelist()

            if "manifest.json" not in names:
                issues.append("manifest.json is missing")
            else:
                manifest = PackManifest.model_validate_json(zf.read("manifest.json"))
                for entry in manifest.samples:
                    if f"samples/{entry.filename}" not in names:
                        issues.append(f"Missing file in archive: {entry.filename}")
    except Exception as e:
        issues.append(f"ZIP error: {e}")

    ok = len(issues) == 0
    result = {"valid": ok, "issues": issues}

    if as_json:
        print(json.dumps(result))
    elif ok:
        console.print("[green]Pack is valid.[/green]")
    else:
        console.print("[red]Pack has issues:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")


@pack_app.command("list")
def pack_list(
    pack_path: Path = typer.Argument(..., help="Path to the .smpack file"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Show the contents of a .smpack file without importing it."""
    import zipfile

    with zipfile.ZipFile(pack_path, "r") as zf:
        manifest = PackManifest.model_validate_json(zf.read("manifest.json"))

    if as_json:
        print(manifest.model_dump_json(indent=2))
        return

    console.print(f"[bold]{manifest.name}[/bold] v{manifest.version} by {manifest.author}")
    console.print(f"  {manifest.description}")
    console.print(f"  Samples: {len(manifest.samples)}")

    table = Table(show_header=True)
    table.add_column("Filename")
    table.add_column("BPM")
    table.add_column("Key")
    table.add_column("Instrument")
    table.add_column("Energy")

    for s in manifest.samples:
        table.add_row(
            s.filename,
            str(int(s.bpm)) if s.bpm else "–",
            s.key or "–",
            s.instrument or "–",
            s.energy or "–",
        )

    console.print(table)
```

Register `pack_app` in the main CLI app:

```python
# filename: src/samplemind/cli/app.py  (addition)

from samplemind.cli.commands.pack import pack_app

# Add alongside existing app.add_typer() calls:
app.add_typer(pack_app, name="pack")
```

---

## 6. GitHub Releases — Distribution

```bash
# filename: scripts/release-pack.sh

#!/usr/bin/env bash
# Usage: ./scripts/release-pack.sh trap-essentials-v1 "Trap Essentials Vol. 1"

set -euo pipefail

SLUG="$1"
NAME="$2"
PACK_FILE="${SLUG}.smpack"

echo "Creating pack: ${PACK_FILE}"
uv run samplemind pack create "${NAME}" "${SLUG}" --output .

echo "Creating GitHub Release: ${SLUG}"
gh release create "${SLUG}" \
    --title "${NAME}" \
    --notes "Sample pack: ${NAME}" \
    "${PACK_FILE}"

echo "Done: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/tag/${SLUG}"
```

---

## 7. Community Registry Concept

A future `registry.json` for official packs:

```json
{
  "registry_version": "1",
  "updated_at": "2025-10-01T12:00:00Z",
  "packs": [
    {
      "name": "Trap Essentials Vol. 1",
      "slug": "trap-essentials-v1",
      "version": "1.0.0",
      "author": "SampleMind",
      "tags": ["trap", "808"],
      "download_url": "https://github.com/username/samplemind-packs/releases/download/trap-essentials-v1/trap-essentials-v1.smpack",
      "sha256": "abc123..."
    }
  ]
}
```

---

## 8. Tests

```python
# filename: tests/test_packs.py

import json
import zipfile
from pathlib import Path
import pytest
import numpy as np
import soundfile as sf

from samplemind.packs.manifest import PackManifest, SampleEntry, compute_sha256
from samplemind.packs.exporter import export_pack
from samplemind.packs.importer import import_pack


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    """Create a minimal WAV file for testing."""
    wav_path = tmp_path / "kick_120bpm.wav"
    samples = np.zeros(22050, dtype=np.float32)  # 1 second of silence
    sf.write(str(wav_path), samples, 22050)
    return wav_path


def test_compute_sha256(sample_wav: Path):
    sha = compute_sha256(sample_wav)
    assert len(sha) == 64      # SHA-256 produces 64 hex characters
    assert sha == compute_sha256(sample_wav)  # Must be deterministic


def test_manifest_serialization():
    """PackManifest should serialize and deserialize without data loss."""
    manifest = PackManifest(
        name="Test Pack",
        slug="test-pack",
        samples=[
            SampleEntry(filename="kick.wav", sha256="a" * 64, bpm=128.0)
        ],
    )
    json_str = manifest.model_dump_json()
    restored = PackManifest.model_validate_json(json_str)
    assert restored.name == "Test Pack"
    assert restored.samples[0].bpm == 128.0


def test_roundtrip(tmp_path: Path, sample_wav: Path, monkeypatch):
    """
    Full roundtrip: exporter → ZIP → importer.
    Uses monkeypatch to override SampleRepository.search().
    """
    from samplemind import models

    # Create a minimal Sample instance
    sample = models.Sample(
        id=1,
        filename=sample_wav.name,
        path=str(sample_wav),
        bpm=128.0,
        key="C min",
        instrument="kick",
        mood="dark",
        energy="high",
        duration=1.0,
    )

    from samplemind.data import repository as repo_module

    class MockRepo:
        def search(self, **_):
            return [sample]
        def get_by_name(self, _):
            return None
        def upsert(self, *args, **kwargs):
            pass

    monkeypatch.setattr(repo_module, "SampleRepository", MockRepo)

    # Export
    pack_path = tmp_path / "test.smpack"
    manifest = export_pack("Test Pack", "test-pack", pack_path, skip_analysis=True)

    assert pack_path.exists()
    assert len(manifest.samples) == 1

    # Verify ZIP contents
    with zipfile.ZipFile(pack_path) as zf:
        assert "manifest.json" in zf.namelist()
        assert f"samples/{sample_wav.name}" in zf.namelist()

    # Import
    dest = tmp_path / "imported"
    result = import_pack(pack_path, dest, verify_checksums=True, skip_analysis=True)

    assert result["imported"] == 1
    assert result["errors"] == 0
    assert (dest / sample_wav.name).exists()
```

---

## Migration Notes

- New modules live under `src/samplemind/packs/` — nothing is deleted
- `pack_app` is registered in `app.py` via `app.add_typer(pack_app, name="pack")`
- Add to `pyproject.toml`: `pydantic >= 2.7` (already a transitive dependency via SQLModel)
- No database migration needed — the existing `Sample` table is used unchanged

---

## Testing Checklist

```bash
# Create a test pack from all kick samples
$ uv run samplemind pack create "Kick Collection" kick-collection-v1 \
    --instrument kick --energy high --author "Test"

# Validate the pack without importing
$ uv run samplemind pack verify kick-collection-v1.smpack

# List pack contents
$ uv run samplemind pack list kick-collection-v1.smpack

# Import to a temporary folder
$ uv run samplemind pack import kick-collection-v1.smpack --dest /tmp/pack-test

# Run unit tests
$ uv run pytest tests/test_packs.py -v
```

---

## Troubleshooting

**`ValueError: No samples matched the filter`**
```bash
# Check that samples exist in the database:
$ uv run samplemind list
# If empty, run import first:
$ uv run samplemind import ~/Music/Samples/
```

**SHA-256 checksum fails on import**
```
This usually means the WAV file was modified after the pack was created.
Use --no-verify to skip the check, but be aware the file may be corrupted.
```

**`PackImportError: Unknown format version: 2`**
```
The pack was created with a newer version of SampleMind.
Upgrade with: uv tool upgrade samplemind
```

---

## 7. Sample Pack Distribution (2026)

### SHA-256 Integrity Verification

Every `.smpack` file includes per-sample SHA-256 hashes in its manifest, verified on import:

```python
# src/samplemind/packs/importer.py
import hashlib
import json
import zipfile
from pathlib import Path


def verify_pack(pack_path: Path) -> tuple[bool, list[str]]:
    """Verify SHA-256 integrity of all samples in a .smpack file.

    Returns (is_valid, list_of_errors).
    """
    errors = []
    with zipfile.ZipFile(pack_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        for entry in manifest.get("samples", []):
            filename = entry["filename"]
            expected = entry.get("sha256")
            if not expected:
                errors.append(f"{filename}: missing sha256 in manifest")
                continue
            try:
                data = zf.read(filename)
                actual = hashlib.sha256(data).hexdigest()
                if actual != expected:
                    errors.append(f"{filename}: checksum mismatch (expected {expected[:8]}..., got {actual[:8]}...)")
            except KeyError:
                errors.append(f"{filename}: file missing from archive")

    return len(errors) == 0, errors


def import_pack(pack_path: Path, dest_dir: Path) -> dict:
    """Import a .smpack file after verifying integrity."""
    is_valid, errors = verify_pack(pack_path)
    if not is_valid:
        raise ValueError(f"Pack integrity check failed:\n" + "\n".join(errors))

    # Extract and import samples...
    with zipfile.ZipFile(pack_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        extracted = []
        for entry in manifest["samples"]:
            out_path = dest_dir / entry["filename"]
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(zf.read(entry["filename"]))
            extracted.append(out_path)
    return {"extracted": len(extracted), "pack": manifest["name"]}
```

### Pack Versioning

`manifest.json` uses semantic versioning:

```json
{
  "name": "Dark Trap Essentials",
  "slug": "dark-trap-essentials",
  "version": "1.2.0",
  "min_samplemind": "0.3.0",
  "created_at": "2026-03-25T00:00:00Z",
  "author": "SampleMind",
  "description": "85 dark trap samples: kicks, 808s, snares, hihats",
  "tags": ["trap", "dark", "808"],
  "sample_count": 85,
  "samples": [
    {
      "filename": "kicks/kick_808_128bpm.wav",
      "sha256": "a1b2c3d4...",
      "bpm": 128.0,
      "key": "C min",
      "instrument": "kick",
      "mood": "dark",
      "energy": "high",
      "duration": 0.45
    }
  ]
}
```

Validate `min_samplemind` version on import:
```python
from importlib.metadata import version
from packaging.version import Version

def check_compatibility(manifest: dict) -> None:
    min_ver = manifest.get("min_samplemind", "0.0.0")
    current = version("samplemind")
    if Version(current) < Version(min_ver):
        raise RuntimeError(
            f"This pack requires SampleMind >= {min_ver} (you have {current}). "
            f"Run: uv add samplemind>={min_ver}"
        )
```

### Release Script

```bash
#!/bin/bash
# scripts/release-pack.sh
# Usage: ./scripts/release-pack.sh dark-trap-essentials 1.2.0
set -euo pipefail

PACK_SLUG="${1:?Usage: $0 <slug> <version>}"
VERSION="${2:?Usage: $0 <slug> <version>}"
PACK_FILE="dist/${PACK_SLUG}-${VERSION}.smpack"

echo "Building pack: ${PACK_SLUG} v${VERSION}..."
uv run samplemind pack create "${PACK_SLUG}" --version "${VERSION}" --output "${PACK_FILE}"

echo "Verifying pack integrity..."
uv run python -c "
from samplemind.packs.importer import verify_pack
from pathlib import Path
ok, errors = verify_pack(Path('${PACK_FILE}'))
if not ok:
    print('ERRORS:', errors)
    exit(1)
print('Integrity OK')
"

echo "Computing SHA-256 of pack file..."
PACK_SHA=$(sha256sum "${PACK_FILE}" | cut -d' ' -f1)
echo "${PACK_SHA}  ${PACK_SLUG}-${VERSION}.smpack" > "${PACK_FILE}.sha256"

echo "Creating GitHub Release..."
gh release create "pack-${PACK_SLUG}-${VERSION}" \
  "${PACK_FILE}" \
  "${PACK_FILE}.sha256" \
  --title "${PACK_SLUG} v${VERSION}" \
  --notes "### ${PACK_SLUG} v${VERSION}

Sample pack release.

**SHA-256:** \`${PACK_SHA}\`

Install with:
\`\`\`bash
uv run samplemind pack import ${PACK_SLUG}-${VERSION}.smpack
\`\`\`"

echo "Released: pack-${PACK_SLUG}-${VERSION}"
```

### Pack Registry (Future)

A JSON index for the in-app pack browser (Phase 10+):

```json
{
  "registry_version": "1",
  "updated_at": "2026-03-25T00:00:00Z",
  "packs": [
    {
      "slug": "dark-trap-essentials",
      "name": "Dark Trap Essentials",
      "version": "1.2.0",
      "description": "85 dark trap samples",
      "tags": ["trap", "dark"],
      "sample_count": 85,
      "download_url": "https://github.com/lchtangen/SampleMind-AI/releases/download/pack-dark-trap-essentials-1.2.0/dark-trap-essentials-1.2.0.smpack",
      "sha256_url": "...sha256"
    }
  ]
}
```

CLI command to browse registry:
```bash
uv run samplemind pack list          # list available packs from registry
uv run samplemind pack search trap   # search registry
uv run samplemind pack install dark-trap-essentials  # download + import
```

