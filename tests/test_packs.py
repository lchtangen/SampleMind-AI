"""Integration tests for the .smpack sample pack format.

Covers:
  - checksum_file() stability and uniqueness
  - verify_entry() pass/fail
  - PackEntry and PackManifest Pydantic validation
  - create_pack() ZIP structure and manifest accuracy
  - import_pack() full round-trip including DB upsert
  - import_pack(dry_run=True) verify-only path
  - Integrity error on tampered file
  - Error handling for missing/invalid inputs
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from samplemind.packs.builder import PackBuildError, create_pack
from samplemind.packs.checksums import checksum_file, verify_entry, verify_manifest_checksums
from samplemind.packs.importer import PackIntegrityError, import_pack
from samplemind.packs.models import PackEntry, PackManifest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_wav_dir(tmp_path: Path, n: int = 1, fixture_wav: Path | None = None) -> Path:
    """Create a temp directory with n WAV files."""
    d = tmp_path / "wavs"
    d.mkdir()
    for i in range(n):
        if fixture_wav:
            shutil.copy(fixture_wav, d / f"sample_{i}.wav")
        else:
            # minimal valid WAV: 44-byte header + silence
            (d / f"sample_{i}.wav").write_bytes(b"\x00" * 44 + bytes(range(i, i + 64)))
    return d


def _pack_meta(name: str = "Test Pack", version: str = "1.0.0") -> dict:
    return {
        "name": name,
        "version": version,
        "author": "testdev",
        "description": "Automated test pack",
    }


# ── checksum_file ─────────────────────────────────────────────────────────────

def test_checksum_file_stable(tmp_path: Path) -> None:
    """Same file produces the same hex digest on repeated calls."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"SampleMind test data " * 100)
    assert checksum_file(f) == checksum_file(f)


def test_checksum_file_unique(tmp_path: Path) -> None:
    """Two files with different contents produce different digests."""
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"alpha content")
    b.write_bytes(b"beta content")
    assert checksum_file(a) != checksum_file(b)


def test_checksum_file_hex_format(tmp_path: Path) -> None:
    """Digest is 64-character lowercase hex string."""
    f = tmp_path / "f.bin"
    f.write_bytes(b"test")
    digest = checksum_file(f)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


# ── verify_entry ─────────────────────────────────────────────────────────────

def test_verify_entry_pass(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"wav content 123")
    entry = PackEntry(filename="audio.wav", sha256=checksum_file(f), size_bytes=f.stat().st_size)
    assert verify_entry(entry, f) is True


def test_verify_entry_fail_after_tamper(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"original content")
    entry = PackEntry(filename="audio.wav", sha256=checksum_file(f), size_bytes=f.stat().st_size)
    f.write_bytes(b"tampered content")
    assert verify_entry(entry, f) is False


# ── PackEntry validation ──────────────────────────────────────────────────────

def test_pack_entry_energy_valid() -> None:
    for e in ("low", "mid", "high"):
        entry = PackEntry(filename="f.wav", sha256="a" * 64, size_bytes=100, energy=e)
        assert entry.energy == e


def test_pack_entry_energy_invalid() -> None:
    with pytest.raises(ValidationError, match="energy"):
        PackEntry(filename="f.wav", sha256="a" * 64, size_bytes=100, energy="ultra")


def test_pack_entry_sha256_must_be_64_hex() -> None:
    with pytest.raises(ValidationError, match="sha256"):
        PackEntry(filename="f.wav", sha256="a" * 63, size_bytes=100)


def test_pack_entry_sha256_normalised_to_lowercase() -> None:
    entry = PackEntry(filename="f.wav", sha256="A" * 64, size_bytes=100)
    assert entry.sha256 == "a" * 64


# ── PackManifest validation ───────────────────────────────────────────────────

def test_pack_manifest_version_valid() -> None:
    m = PackManifest(
        name="x", version="2.3.4", author="a", description="d",
        created_at="2026-01-01T00:00:00Z", entries=[],
    )
    assert m.version == "2.3.4"


def test_pack_manifest_version_invalid() -> None:
    with pytest.raises(ValidationError, match="semver"):
        PackManifest(
            name="x", version="bad", author="a", description="d",
            created_at="2026-01-01T00:00:00Z", entries=[],
        )


def test_pack_manifest_total_size(tmp_path: Path) -> None:
    entries = [
        PackEntry(filename="a.wav", sha256="a" * 64, size_bytes=1000),
        PackEntry(filename="b.wav", sha256="b" * 64, size_bytes=2000),
    ]
    m = PackManifest(name="x", version="1.0.0", author="a", description="d",
                     created_at="2026-01-01T00:00:00Z", entries=entries)
    assert m.total_size_bytes == 3000
    assert m.entry_count == 2


# ── create_pack ───────────────────────────────────────────────────────────────

def test_create_pack_structure(tmp_path: Path, silent_wav: Path) -> None:
    """Created archive must contain manifest.json and the WAV file."""
    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    out = create_pack(wav_dir, **_pack_meta())
    assert out.suffix == ".smpack"
    assert zipfile.is_zipfile(out)
    with zipfile.ZipFile(out) as zf:
        assert "manifest.json" in zf.namelist()
        wav_entries = [n for n in zf.namelist() if n.endswith(".wav")]
        assert len(wav_entries) == 1


def test_create_pack_manifest_content(tmp_path: Path, silent_wav: Path) -> None:
    """Manifest entries must match the source files with correct checksums."""
    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    out = create_pack(wav_dir, **_pack_meta())
    with zipfile.ZipFile(out) as zf:
        manifest = PackManifest.model_validate_json(zf.read("manifest.json"))
    assert manifest.entry_count == 1
    assert manifest.name == "Test Pack"
    entry = manifest.entries[0]
    # Checksum in manifest must match actual source file
    src = next(wav_dir.rglob("*.wav"))
    assert entry.sha256 == checksum_file(src)
    assert entry.size_bytes == src.stat().st_size


def test_create_pack_with_metadata_overrides(tmp_path: Path, silent_wav: Path) -> None:
    """Metadata overrides must be embedded in the manifest entry."""
    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    wav_name = next(wav_dir.rglob("*.wav")).name
    out = create_pack(
        wav_dir, **_pack_meta(),
        metadata_overrides={wav_name: {"bpm": 128.0, "energy": "high", "instrument": "kick"}},
    )
    with zipfile.ZipFile(out) as zf:
        manifest = PackManifest.model_validate_json(zf.read("manifest.json"))
    entry = manifest.entries[0]
    assert entry.bpm == 128.0
    assert entry.energy == "high"
    assert entry.instrument == "kick"


def test_create_pack_no_wav_raises(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(PackBuildError, match="No WAV"):
        create_pack(empty_dir, **_pack_meta())


def test_create_pack_output_path_override(tmp_path: Path, silent_wav: Path) -> None:
    """When output_path is given, the file must be at exactly that path."""
    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    custom = tmp_path / "my_custom.smpack"
    out = create_pack(wav_dir, **_pack_meta(), output_path=custom)
    assert out == custom.resolve()
    assert custom.exists()


# ── import_pack ───────────────────────────────────────────────────────────────

def test_import_pack_succeeds(tmp_path: Path, silent_wav: Path, orm_engine) -> None:
    """Full round-trip: create pack → import → sample present in DB."""
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    smpack = create_pack(wav_dir, **_pack_meta(), output_path=tmp_path / "pack.smpack")

    dest = tmp_path / "imported"
    samples = import_pack(smpack, dest_dir=dest)

    assert len(samples) == 1
    assert samples[0].filename == next(wav_dir.rglob("*.wav")).name
    assert (dest / samples[0].filename).exists()


def test_import_pack_dry_run(tmp_path: Path, silent_wav: Path) -> None:
    """dry_run=True must verify checksums but return empty list and not copy files."""
    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    smpack = create_pack(wav_dir, **_pack_meta(), output_path=tmp_path / "pack.smpack")
    dest = tmp_path / "should_not_exist"

    samples = import_pack(smpack, dest_dir=dest, dry_run=True)

    assert samples == []
    assert not dest.exists()


def test_import_pack_checksum_tampered(tmp_path: Path, silent_wav: Path) -> None:
    """Tampered WAV must raise PackIntegrityError."""
    wav_dir = _make_wav_dir(tmp_path, n=1, fixture_wav=silent_wav)
    smpack = create_pack(wav_dir, **_pack_meta(), output_path=tmp_path / "pack.smpack")

    # Tamper: replace the WAV inside the ZIP with different bytes
    tampered = tmp_path / "tampered.smpack"
    with zipfile.ZipFile(smpack, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for item in zin.infolist():
            if item.filename.endswith(".wav"):
                zout.writestr(item, b"tampered audio data")
            else:
                zout.writestr(item, zin.read(item.filename))

    with pytest.raises(PackIntegrityError, match="Integrity check failed"):
        import_pack(tampered, dest_dir=tmp_path / "dest")


def test_import_pack_missing_manifest(tmp_path: Path, silent_wav: Path) -> None:
    """ZIP without manifest.json must raise ValueError."""
    no_manifest = tmp_path / "no_manifest.smpack"
    with zipfile.ZipFile(no_manifest, "w") as zf:
        zf.writestr("audio.wav", b"fake wav")

    with pytest.raises(ValueError, match="manifest.json"):
        import_pack(no_manifest)


def test_import_pack_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        import_pack(tmp_path / "nonexistent.smpack")


def test_import_pack_not_a_zip(tmp_path: Path) -> None:
    bad = tmp_path / "bad.smpack"
    bad.write_bytes(b"this is not a zip file")
    with pytest.raises(ValueError, match="valid"):
        import_pack(bad)


def test_import_pack_multiple_files(tmp_path: Path, silent_wav: Path, orm_engine) -> None:
    """Import should handle packs with multiple WAV files."""
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    wav_dir = _make_wav_dir(tmp_path, n=3, fixture_wav=silent_wav)
    smpack = create_pack(wav_dir, **_pack_meta(), output_path=tmp_path / "pack.smpack")
    samples = import_pack(smpack, dest_dir=tmp_path / "imported")
    assert len(samples) == 3


# ── verify_manifest_checksums ─────────────────────────────────────────────────

def test_verify_manifest_checksums_all_pass(tmp_path: Path) -> None:
    f = tmp_path / "a.wav"
    f.write_bytes(b"content")
    entry = PackEntry(filename="a.wav", sha256=checksum_file(f), size_bytes=f.stat().st_size)
    manifest = PackManifest(name="t", version="1.0.0", author="a", description="d",
                            created_at="2026-01-01T00:00:00Z", entries=[entry])
    failures = verify_manifest_checksums(manifest, tmp_path)
    assert failures == []


def test_verify_manifest_checksums_missing_file(tmp_path: Path) -> None:
    entry = PackEntry(filename="missing.wav", sha256="a" * 64, size_bytes=100)
    manifest = PackManifest(name="t", version="1.0.0", author="a", description="d",
                            created_at="2026-01-01T00:00:00Z", entries=[entry])
    failures = verify_manifest_checksums(manifest, tmp_path)
    assert len(failures) == 1
    assert "missing" in failures[0].lower()
