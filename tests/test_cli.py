"""
tests/test_cli.py — Integration tests for all Typer CLI commands.

Strategy
--------
* CliRunner(mix_stderr=False) keeps stdout/stderr separate so JSON assertions
  can target stdout directly, matching the Tauri IPC contract.
* analyze_file() is monkeypatched to return a fixed dict — avoids slow librosa
  and makes tests deterministic.  Parallel batch workers are set to 1 to keep
  ProcessPoolExecutor from conflicting with pytest-xdist workers.
* All tests share the orm_engine fixture (in-memory SQLite via conftest.py)
  which is re-injected into samplemind.data.orm._engine so that init_orm()
  inside each command uses the test database.
* WAV fixtures (silent_wav, kick_wav) from conftest.py provide real files on
  disk when commands need an actual path.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from samplemind.cli.app import app
from samplemind.core.models.sample import SampleCreate
from samplemind.data.repositories.sample_repository import SampleRepository

if TYPE_CHECKING:
    from sqlalchemy import Engine

# ── Test runner ───────────────────────────────────────────────────────────────

runner = CliRunner()

# ── Fixed analysis stub ───────────────────────────────────────────────────────

_MOCK_ANALYSIS: dict = {
    "bpm": 128.0,
    "key": "C maj",
    "energy": "high",
    "mood": "dark",
    "instrument": "kick",
}


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _redirect_orm(orm_engine: Engine) -> None:
    """Point every CLI command at the in-memory test engine."""
    import samplemind.data.orm as orm_module

    orm_module._engine = orm_engine


@pytest.fixture()
def mock_analyze(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace analyze_file with a fast stub returning _MOCK_ANALYSIS."""
    monkeypatch.setattr(
        "samplemind.cli.commands.analyze.analyze_file",
        lambda _path: dict(_MOCK_ANALYSIS),
    )
    # Patch inside batch.py so ProcessPoolExecutor picks up the stub
    monkeypatch.setattr(
        "samplemind.analyzer.batch.analyze_file",
        lambda _path: dict(_MOCK_ANALYSIS),
    )


# ── version ───────────────────────────────────────────────────────────────────


def test_version_prints_version() -> None:
    """samplemind version should print the package version string."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0." in result.output  # matches "0.2.0" etc.


# ── import ────────────────────────────────────────────────────────────────────


def test_import_nonexistent_folder_json() -> None:
    """import --json on a missing folder should print an error JSON and exit non-zero."""
    result = runner.invoke(app, ["import", "/does/not/exist/at/all", "--json"])
    assert result.exit_code != 0
    data = json.loads(result.stdout)
    assert "error" in data


def test_import_empty_folder_json(tmp_path: Path) -> None:
    """import --json on a folder with no WAV files returns imported=0."""
    result = runner.invoke(app, ["import", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["imported"] == 0
    assert data["errors"] == 0
    assert data["samples"] == []


def test_import_wav_folder_json(tmp_path: Path, silent_wav: Path, mock_analyze: None) -> None:
    """import --json on a folder with a WAV file returns imported=1."""
    folder = tmp_path / "import_input"
    folder.mkdir()
    shutil.copy(silent_wav, folder / "test_kick.wav")

    result = runner.invoke(app, ["import", str(folder), "--json", "--workers", "1"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["imported"] == 1
    assert data["errors"] == 0
    assert len(data["samples"]) == 1


def test_import_json_schema(tmp_path: Path, silent_wav: Path, mock_analyze: None) -> None:
    """import --json sample objects must contain id, filename, bpm fields."""
    folder = tmp_path / "import_schema"
    folder.mkdir()
    shutil.copy(silent_wav, folder / "kick.wav")

    result = runner.invoke(app, ["import", str(folder), "--json", "--workers", "1"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["samples"]) == 1
    s = data["samples"][0]
    assert "id" in s
    assert "filename" in s
    assert "bpm" in s


def test_import_with_workers(tmp_path: Path, silent_wav: Path, mock_analyze: None) -> None:
    """import --workers 1 should succeed (serial mode, monkeypatch-compatible)."""
    folder = tmp_path / "import_workers"
    folder.mkdir()
    shutil.copy(silent_wav, folder / "kick.wav")
    result = runner.invoke(app, ["import", str(folder), "--workers", "1", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["imported"] == 1


# ── analyze ───────────────────────────────────────────────────────────────────


def test_analyze_nonexistent_folder() -> None:
    """analyze on a missing folder should exit non-zero."""
    result = runner.invoke(app, ["analyze", "/no/such/folder"])
    assert result.exit_code != 0


def test_analyze_json_output(tmp_path: Path, silent_wav: Path, mock_analyze: None) -> None:
    """analyze --json should return a list of analysis dicts."""
    # Use a dedicated sub-folder to avoid picking up the silent_wav fixture file
    folder = tmp_path / "analyze_input"
    folder.mkdir()
    shutil.copy(silent_wav, folder / "sample.wav")

    result = runner.invoke(app, ["analyze", str(folder), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["bpm"] == 128.0


# ── list ──────────────────────────────────────────────────────────────────────


def test_list_empty_library_json() -> None:
    """list --json on an empty library returns an empty samples array."""
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["samples"] == []
    assert data["total"] == 0


def test_list_returns_samples_json() -> None:
    """list --json after adding a sample should include that sample."""
    SampleRepository.upsert(SampleCreate(filename="hi.wav", path="/hi.wav", bpm=140.0))
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["samples"]) == 1
    assert data["samples"][0]["filename"] == "hi.wav"


# ── search ────────────────────────────────────────────────────────────────────


def test_search_no_args_returns_json_array() -> None:
    """search --json with no filters returns samples dict with samples key."""
    result = runner.invoke(app, ["search", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "samples" in data
    assert isinstance(data["samples"], list)


def test_search_energy_filter_json() -> None:
    """search --energy high --json returns only high-energy samples."""
    SampleRepository.upsert(SampleCreate(filename="hi.wav", path="/hi.wav", energy="high"))
    SampleRepository.upsert(SampleCreate(filename="lo.wav", path="/lo.wav", energy="low"))
    result = runner.invoke(app, ["search", "--energy", "high", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    samples = data["samples"]
    assert all(s["energy"] == "high" for s in samples)
    assert len(samples) == 1


def test_search_instrument_filter_json() -> None:
    """search --instrument kick --json returns only kick samples."""
    SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/kick.wav", instrument="kick"))
    SampleRepository.upsert(SampleCreate(filename="snare.wav", path="/snare.wav", instrument="snare"))
    result = runner.invoke(app, ["search", "--instrument", "kick", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    samples = data["samples"]
    assert len(samples) == 1
    assert samples[0]["instrument"] == "kick"


# ── tag ───────────────────────────────────────────────────────────────────────


def test_tag_invalid_energy_exits_1() -> None:
    """tag with an invalid energy value (not low/mid/high) should exit 1."""
    result = runner.invoke(app, ["tag", "somefile", "--energy", "ultra"])
    assert result.exit_code != 0


def test_tag_unknown_sample_exits_1() -> None:
    """tag for a sample that doesn't exist in the library should exit 1."""
    result = runner.invoke(app, ["tag", "definitely_not_in_db_xyz"])
    assert result.exit_code != 0


def test_tag_updates_genre() -> None:
    """tag --genre should persist the genre on the matching sample."""
    SampleRepository.upsert(SampleCreate(filename="dark_kick.wav", path="/dark_kick.wav"))
    result = runner.invoke(app, ["tag", "dark_kick", "--genre", "trap"])
    assert result.exit_code == 0
    s = SampleRepository.get_by_name("dark_kick")
    assert s is not None
    assert s.genre == "trap"


# ── stats ─────────────────────────────────────────────────────────────────────


def test_stats_empty_json() -> None:
    """stats --json on an empty library returns total=0."""
    result = runner.invoke(app, ["stats", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["total"] == 0
    assert data["bpm"] is None


def test_stats_with_data_json() -> None:
    """stats --json with samples returns correct totals."""
    SampleRepository.upsert(SampleCreate(filename="a.wav", path="/a.wav", bpm=120.0, energy="high"))
    SampleRepository.upsert(SampleCreate(filename="b.wav", path="/b.wav", bpm=140.0, energy="mid"))
    result = runner.invoke(app, ["stats", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["total"] == 2
    assert data["with_bpm"] == 2


def test_stats_json_schema() -> None:
    """stats --json output must include all required top-level keys."""
    result = runner.invoke(app, ["stats", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    for key in ("total", "with_bpm", "without_bpm", "by_energy", "by_instrument", "by_mood"):
        assert key in data, f"Missing key: {key}"


# ── duplicates ────────────────────────────────────────────────────────────────


def test_duplicates_empty_library() -> None:
    """duplicates on an empty library exits 0 (nothing to report)."""
    result = runner.invoke(app, ["duplicates"])
    assert result.exit_code == 0


def test_duplicates_no_dupes_exits_0(tmp_path: Path, silent_wav: Path) -> None:
    """duplicates with no duplicate files exits 0."""
    wav = tmp_path / "unique.wav"
    shutil.copy(silent_wav, wav)
    SampleRepository.upsert(SampleCreate(filename=wav.name, path=str(wav)))
    result = runner.invoke(app, ["duplicates"])
    assert result.exit_code == 0


def test_duplicates_found_exits_1(tmp_path: Path, silent_wav: Path) -> None:
    """duplicates with duplicate files exits 1 (signal for CI)."""
    wav1 = tmp_path / "kick_a.wav"
    wav2 = tmp_path / "kick_b.wav"
    shutil.copy(silent_wav, wav1)
    shutil.copy(silent_wav, wav2)  # identical content → same SHA-256
    SampleRepository.upsert(SampleCreate(filename=wav1.name, path=str(wav1)))
    SampleRepository.upsert(SampleCreate(filename=wav2.name, path=str(wav2)))
    result = runner.invoke(app, ["duplicates"])
    assert result.exit_code == 1


def test_duplicates_remove_deletes_extra(tmp_path: Path, silent_wav: Path) -> None:
    """duplicates --remove should delete the duplicate file and its DB row."""
    wav1 = tmp_path / "kick_a.wav"
    wav2 = tmp_path / "kick_b.wav"
    shutil.copy(silent_wav, wav1)
    shutil.copy(silent_wav, wav2)
    SampleRepository.upsert(SampleCreate(filename=wav1.name, path=str(wav1)))
    SampleRepository.upsert(SampleCreate(filename=wav2.name, path=str(wav2)))
    result = runner.invoke(app, ["duplicates", "--remove"])
    assert result.exit_code == 0
    # After removal only one of the two files should still exist
    still_exist = sum(1 for w in (wav1, wav2) if w.exists())
    assert still_exist == 1


# ── export ────────────────────────────────────────────────────────────────────


def test_export_no_samples_creates_target_folder(tmp_path: Path) -> None:
    """export with no matching samples still creates the target folder."""
    target = tmp_path / "out"
    result = runner.invoke(app, ["export", "--target", str(target), "--energy", "high"])
    assert result.exit_code == 0
    assert target.is_dir()


def test_export_copies_files(tmp_path: Path, silent_wav: Path) -> None:
    """export copies files matching the filter into the target folder."""
    # Register a real file in the library
    wav = tmp_path / "src" / "kick.wav"
    wav.parent.mkdir()
    shutil.copy(silent_wav, wav)
    SampleRepository.upsert(
        SampleCreate(filename=wav.name, path=str(wav), energy="high", instrument="kick")
    )

    target = tmp_path / "export"
    result = runner.invoke(
        app, ["export", "--target", str(target), "--instrument", "kick"]
    )
    assert result.exit_code == 0
    exported = list(target.rglob("*.wav"))
    assert len(exported) == 1
