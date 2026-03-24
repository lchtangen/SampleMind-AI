# Fase 9 — Sample-pakker (.smpack)

> Bygg et pakkeformat for å eksportere, dele og importere kuraterte sample-biblioteker som én fil.

---

## Forutsetninger

- Fase 1–8 fullført
- `uv`, `pyproject.toml`, SQLModel og Typer er satt opp
- Grunnleggende forståelse av ZIP-filer og JSON

---

## Mål etter denne fasen

- `.smpack`-format definert (ZIP med `manifest.json` + `samples/`)
- `PackManifest` Pydantic-modell med versjonering og SHA-256-sjekksummer
- CLI-kommandoer: `samplemind pack create|export|import|list|verify`
- Idempotent import (duplikater unngås automatisk)
- GitHub Releases-distribusjon via `gh`-verktøyet

---

## 1. Pakkeformat

En `.smpack`-fil er en ZIP-arkiv med følgende struktur:

```
my-pack.smpack          ← ZIP-fil med nytt navn
├── manifest.json       ← Metadata og sample-liste
└── samples/
    ├── kick_128bpm_Cmin.wav
    ├── snare_trap_96bpm.wav
    └── bass_Fmaj.wav
```

### manifest.json — eksempel

```json
{
  "name": "Trap Essentials Vol. 1",
  "slug": "trap-essentials-v1",
  "version": "1.0.0",
  "format_version": "1",
  "author": "SampleMind",
  "description": "808-bass, trommer og atmosfærer for trap-produksjon.",
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

## 2. PackManifest — Pydantic-modell

```python
# filename: src/samplemind/packs/manifest.py

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class SampleEntry(BaseModel):
    """Metadata for én sample inne i en pakke."""
    filename: str
    sha256: str                          # SHA-256 av WAV-filen
    bpm: Optional[float] = None
    key: Optional[str] = None
    instrument: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    duration: Optional[float] = None


class PackManifest(BaseModel):
    """
    Toppnivå-modell for .smpack manifest.
    format_version = "1" → bump om JSON-strukturen endres.
    """
    name: str
    slug: str                            # URL-vennlig identifikator: "trap-essentials-v1"
    version: str = "1.0.0"              # Semver for pakke-innholdet
    format_version: str = "1"           # Semver for selve formatet
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
    """Beregn SHA-256-hash for en fil (for integritetssjekk ved import)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
```

---

## 3. Eksportér en pakke

```python
# filename: src/samplemind/packs/exporter.py

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from samplemind.packs.manifest import PackManifest, SampleEntry, compute_sha256
from samplemind.data.repository import SampleRepository


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
    Filtrer biblioteket og eksporter resultatet som en .smpack-fil.

    Returnerer PackManifest-objektet (med SHA-256-sjekksummer).
    """
    repo = SampleRepository()
    samples = repo.search(
        instrument=instrument,
        mood=mood,
        energy=energy,
        tags=tags,
    )

    if not samples:
        raise ValueError("Ingen samples matchet filteret — pakken er tom.")

    entries: list[SampleEntry] = []
    bpm_values: list[float] = []

    # Bygg ZIP-arkiv
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for sample in samples:
            src = Path(sample.path)
            if not src.exists():
                continue

            # SHA-256 for integritetssjekk
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

        # Bygg manifest
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

        # Skriv manifest.json inn i ZIP-en
        manifest_json = manifest.model_dump_json(indent=2)
        zf.writestr("manifest.json", manifest_json)

    return manifest
```

---

## 4. Importer en pakke

```python
# filename: src/samplemind/packs/importer.py

import hashlib
import json
import zipfile
from pathlib import Path

from samplemind.packs.manifest import PackManifest, compute_sha256
from samplemind.data.repository import SampleRepository
from samplemind.analyzer.audio_analysis import analyze_file


class PackImportError(Exception):
    """Kastet ved valideringsfeil under pakke-import."""


def import_pack(
    pack_path: Path,
    dest_dir: Path,
    *,
    verify_checksums: bool = True,
    skip_analysis: bool = False,
) -> dict[str, int]:
    """
    Importer en .smpack-fil til biblioteket.

    - Validerer manifest-format og SHA-256-sjekksummer
    - Kopierer WAV-filer til dest_dir
    - Analyserer og upsert-er hver sample i databasen
    - Idempotent: importerer samme pakke to ganger = ingen duplikater

    Returnerer: {"imported": N, "skipped": M, "errors": K}
    """
    if not pack_path.exists():
        raise PackImportError(f"Fant ikke pakken: {pack_path}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    repo = SampleRepository()

    with zipfile.ZipFile(pack_path, "r") as zf:
        # Les manifest
        try:
            manifest_bytes = zf.read("manifest.json")
        except KeyError:
            raise PackImportError("Ugyldig pakke: manifest.json mangler")

        manifest = PackManifest.model_validate_json(manifest_bytes)

        # Valider format-versjon
        if manifest.format_version != "1":
            raise PackImportError(
                f"Ukjent format-versjon: {manifest.format_version} "
                f"(denne versjonen av SampleMind støtter kun v1)"
            )

        imported = skipped = errors = 0

        for entry in manifest.samples:
            src_name = f"samples/{entry.filename}"
            dest_path = dest_dir / entry.filename

            # Sjekk om sample allerede eksisterer i DB (idempotent)
            existing = repo.get_by_name(entry.filename)
            if existing and dest_path.exists():
                skipped += 1
                continue

            # Pakk ut WAV-fil
            try:
                zf.extract(src_name, dest_dir.parent)
            except KeyError:
                errors += 1
                continue

            # Verifiser SHA-256-sjekksummen
            if verify_checksums:
                actual_sha = compute_sha256(dest_path)
                if actual_sha != entry.sha256:
                    dest_path.unlink(missing_ok=True)
                    errors += 1
                    continue

            # Analyser lydfilen (eller bruk manifest-metadata)
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
                    # Fall tilbake til manifest-metadata
                    metadata = {
                        "bpm": entry.bpm,
                        "key": entry.key,
                        "instrument": entry.instrument,
                        "mood": entry.mood,
                        "energy": entry.energy,
                    }

            repo.upsert(str(dest_path), **metadata)
            imported += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}
```

---

## 5. CLI-kommandoer

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
pack_app = typer.Typer(help="Administrer .smpack sample-pakker.")


@pack_app.command("create")
def pack_create(
    name: str = typer.Argument(..., help="Pakkens navn"),
    slug: str = typer.Argument(..., help="URL-vennlig ID: trap-essentials-v1"),
    output: Path = typer.Option(Path("."), "--output", "-o", help="Mappe for .smpack-filen"),
    instrument: str = typer.Option(None, "--instrument"),
    mood: str = typer.Option(None, "--mood"),
    energy: str = typer.Option(None, "--energy"),
    author: str = typer.Option("Unknown", "--author"),
    description: str = typer.Option("", "--desc"),
    version: str = typer.Option("1.0.0", "--version"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Eksporter et utvalg samples som en .smpack-fil."""
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
        console.print(f"[red]Feil:[/red] {e}", err=True)
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
        console.print(f"[green]Pakke opprettet:[/green] {pack_path}")
        console.print(f"  Samples: {len(manifest.samples)}")
        console.print(f"  Versjon: {manifest.version}")


@pack_app.command("import")
def pack_import(
    pack_path: Path = typer.Argument(..., help="Sti til .smpack-filen"),
    dest: Path = typer.Option(
        Path.home() / "Music" / "SampleMind" / "imported",
        "--dest", "-d",
        help="Mappe for utpakkede WAV-filer",
    ),
    no_verify: bool = typer.Option(False, "--no-verify", help="Hopp over SHA-256-sjekk"),
    skip_analysis: bool = typer.Option(False, "--skip-analysis", help="Bruk manifest-metadata i stedet"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Importer en .smpack-fil til biblioteket."""
    try:
        result = import_pack(
            pack_path,
            dest,
            verify_checksums=not no_verify,
            skip_analysis=skip_analysis,
        )
    except PackImportError as e:
        console.print(f"[red]Import-feil:[/red] {e}", err=True)
        raise typer.Exit(1)

    if as_json:
        print(json.dumps(result))
    else:
        console.print(f"[green]Import fullført:[/green]")
        console.print(f"  Importert: {result['imported']}")
        console.print(f"  Hoppet over (duplikater): {result['skipped']}")
        console.print(f"  Feil: {result['errors']}")


@pack_app.command("verify")
def pack_verify(
    pack_path: Path = typer.Argument(..., help="Sti til .smpack-filen"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Valider en .smpack-fil uten å importere den."""
    import zipfile

    issues: list[str] = []

    if not pack_path.exists():
        console.print(f"[red]Fant ikke filen:[/red] {pack_path}", err=True)
        raise typer.Exit(1)

    try:
        with zipfile.ZipFile(pack_path, "r") as zf:
            names = zf.namelist()

            if "manifest.json" not in names:
                issues.append("manifest.json mangler")
            else:
                manifest = PackManifest.model_validate_json(zf.read("manifest.json"))
                for entry in manifest.samples:
                    if f"samples/{entry.filename}" not in names:
                        issues.append(f"Mangler fil: {entry.filename}")
    except Exception as e:
        issues.append(f"ZIP-feil: {e}")

    ok = len(issues) == 0
    result = {"valid": ok, "issues": issues}

    if as_json:
        print(json.dumps(result))
    elif ok:
        console.print("[green]Pakken er gyldig.[/green]")
    else:
        console.print("[red]Pakken har problemer:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")


@pack_app.command("list")
def pack_list(
    pack_path: Path = typer.Argument(..., help="Sti til .smpack-filen"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Vis innholdet i en .smpack-fil uten å importere den."""
    import zipfile

    with zipfile.ZipFile(pack_path, "r") as zf:
        manifest = PackManifest.model_validate_json(zf.read("manifest.json"))

    if as_json:
        print(manifest.model_dump_json(indent=2))
        return

    console.print(f"[bold]{manifest.name}[/bold] v{manifest.version} av {manifest.author}")
    console.print(f"  {manifest.description}")
    console.print(f"  Samples: {len(manifest.samples)}")

    table = Table(show_header=True)
    table.add_column("Filnavn")
    table.add_column("BPM")
    table.add_column("Toneart")
    table.add_column("Instrument")
    table.add_column("Energi")

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

Registrer `pack_app` i hoved-CLI-appen:

```python
# filename: src/samplemind/cli/app.py  (tillegg)

from samplemind.cli.commands.pack import pack_app

# Legg til under eksisterende app.add_typer()-kall:
app.add_typer(pack_app, name="pack")
```

---

## 6. GitHub Releases — distribusjon

```bash
# filename: scripts/release-pack.sh

#!/usr/bin/env bash
# Bruk: ./scripts/release-pack.sh trap-essentials-v1 "Trap Essentials Vol. 1"

set -euo pipefail

SLUG="$1"
NAME="$2"
PACK_FILE="${SLUG}.smpack"

echo "Lager pakke: ${PACK_FILE}"
uv run samplemind pack create "${NAME}" "${SLUG}" --output .

echo "Oppretter GitHub Release: ${SLUG}"
gh release create "${SLUG}" \
    --title "${NAME}" \
    --notes "Sample-pakke: ${NAME}" \
    "${PACK_FILE}"

echo "Ferdig: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/tag/${SLUG}"
```

---

## 7. Pakke-register (community registry)

Et fremtidig `registry.json` for offisielle pakker:

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

## 8. Tester

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
    """Lag en minimal WAV-fil for testing."""
    wav_path = tmp_path / "kick_120bpm.wav"
    samples = np.zeros(22050, dtype=np.float32)  # 1 sekund stille
    sf.write(str(wav_path), samples, 22050)
    return wav_path


def test_compute_sha256(sample_wav: Path):
    sha = compute_sha256(sample_wav)
    assert len(sha) == 64  # SHA-256 er 64 hex-tegn
    assert sha == compute_sha256(sample_wav)  # Deterministisk


def test_manifest_serialization():
    """PackManifest skal serialisere og deserialisere uten tap."""
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
    Fullt roundtrip: exporter → ZIP → importer.
    Bruker monkeypatch for å overstyre SampleRepository.search().
    """
    from samplemind import models

    # Lag en minimal Sample-instans
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

    # Eksporter
    pack_path = tmp_path / "test.smpack"
    manifest = export_pack("Test Pack", "test-pack", pack_path, skip_analysis=True)

    assert pack_path.exists()
    assert len(manifest.samples) == 1

    # Verifiser ZIP-innhold
    with zipfile.ZipFile(pack_path) as zf:
        assert "manifest.json" in zf.namelist()
        assert f"samples/{sample_wav.name}" in zf.namelist()

    # Importer
    dest = tmp_path / "imported"
    result = import_pack(pack_path, dest, verify_checksums=True, skip_analysis=True)

    assert result["imported"] == 1
    assert result["errors"] == 0
    assert (dest / sample_wav.name).exists()
```

---

## Migrasjonsnotater

- Nye moduler under `src/samplemind/packs/` — ingenting slettes
- `pack_app` legges til i `app.py` med `app.add_typer(pack_app, name="pack")`
- Legg til i `pyproject.toml`: `pydantic >= 2.7` (allerede en avhengighet via SQLModel)
- Ingen database-migrering nødvendig — eksisterende `Sample`-tabellen brukes uendret

---

## Testsjekkliste

```bash
# Lag en testpakke av alle kick-samples
$ uv run samplemind pack create "Kick Collection" kick-collection-v1 \
    --instrument kick --energy high --author "Test"

# Verifiser pakken uten å importere
$ uv run samplemind pack verify kick-collection-v1.smpack

# List innhold
$ uv run samplemind pack list kick-collection-v1.smpack

# Importer til midlertidig mappe
$ uv run samplemind pack import kick-collection-v1.smpack --dest /tmp/pack-test

# Kjør enhetstester
$ uv run pytest tests/test_packs.py -v
```

---

## Feilsøking

**`ValueError: Ingen samples matchet filteret`**
```bash
# Sjekk at det finnes samples i databasen:
$ uv run samplemind list
# Hvis tomt: kjør import først
$ uv run samplemind import ~/Music/Samples/
```

**SHA-256-sjekksummen feiler ved import**
```
Skyldes sannsynligvis at WAV-filen ble endret etter at pakken ble laget.
Bruk --no-verify for å hoppe over sjekken, men vær klar over at filen kan være korrupt.
```

**`PackImportError: Ukjent format-versjon: 2`**
```
Pakken er laget med en nyere versjon av SampleMind.
Oppdater SampleMind med: uv tool upgrade samplemind
```
