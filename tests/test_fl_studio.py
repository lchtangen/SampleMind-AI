"""tests/test_fl_studio.py — Phase 7 FL Studio integration tests.

All tests run without FL Studio installed or any MIDI hardware.
Filesystem tests use pytest's tmp_path fixture for isolation.
Clipboard tests mock subprocess.run to avoid requiring pbcopy/xclip.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── _fl_name() — FL Studio-compatible filename builder ────────────────────────


def _make_sample(**kwargs):
    """Build a minimal Sample-like object using keyword fields."""
    from samplemind.core.models.sample import Sample

    defaults = {
        "filename": "kick.wav",
        "path": "/tmp/kick.wav",
        "bpm": None,
        "key": None,
        "energy": None,
        "instrument": None,
        "mood": None,
    }
    defaults.update(kwargs)
    return Sample(**defaults)


def test_fl_name_full_metadata():
    from samplemind.cli.commands.export import _fl_name

    s = _make_sample(filename="kick.wav", bpm=128.0, key="C maj", energy="high")
    assert _fl_name(s) == "kick_128bpm_C_maj_high.wav"


def test_fl_name_missing_metadata():
    from samplemind.cli.commands.export import _fl_name

    s = _make_sample(filename="loop.wav", bpm=None, key=None, energy=None)
    assert _fl_name(s) == "loop_nobpm_nokey_noenergy.wav"


def test_fl_name_sharp_key_sanitised():
    """# in key becomes 's', spaces become '_'."""
    from samplemind.cli.commands.export import _fl_name

    s = _make_sample(filename="pad.wav", bpm=90.0, key="C# min", energy="low")
    assert _fl_name(s) == "pad_90bpm_Cs_min_low.wav"


def test_fl_name_bpm_rounded():
    """BPM is rounded to the nearest integer in the filename."""
    from samplemind.cli.commands.export import _fl_name

    s = _make_sample(filename="snare.wav", bpm=127.7, key="F min", energy="mid")
    assert _fl_name(s) == "snare_128bpm_F_min_mid.wav"


# ── paths module — no FL Studio installation required ─────────────────────────


def test_fl_studio_path_suffix_contains_expected_segments():
    """_SAMPLES_SUFFIX includes the canonical Patches/Samples/SampleMind path."""
    from samplemind.integrations.paths import _SAMPLES_SUFFIX

    suffix_str = str(_SAMPLES_SUFFIX)
    assert "Patches" in suffix_str
    assert "Samples" in suffix_str
    assert "SampleMind" in suffix_str


def test_fl_versions_includes_fl21():
    """Both FL Studio 20 and FL Studio 21 are probed."""
    from samplemind.integrations.paths import _FL_VERSIONS

    assert "FL Studio" in _FL_VERSIONS
    assert "FL Studio 21" in _FL_VERSIONS


# ── clipboard — mock subprocess so no pbcopy/xclip needed ────────────────────


def test_copy_paths_to_clipboard_macos(tmp_path: Path):
    """On Darwin, pbcopy is invoked with the path text."""
    test_file = tmp_path / "kick.wav"
    test_file.write_bytes(b"RIFF")

    with patch("samplemind.integrations.clipboard.platform.system", return_value="Darwin"), \
         patch("samplemind.integrations.clipboard.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        from samplemind.integrations.clipboard import copy_paths_to_clipboard
        copy_paths_to_clipboard([test_file])

        mock_run.assert_called_once()
        cmd = mock_run.call_args.args[0]
        assert cmd[0] == "pbcopy"


def test_copy_paths_to_clipboard_empty_is_noop():
    """Passing an empty list should not call any subprocess."""
    with patch("samplemind.integrations.clipboard.subprocess.run") as mock_run:
        from samplemind.integrations.clipboard import copy_paths_to_clipboard
        copy_paths_to_clipboard([])
        mock_run.assert_not_called()


# ── filesystem export — real file copy, no FL Studio needed ──────────────────


def test_export_to_fl_studio_copies_file(tmp_path: Path):
    """A real WAV file is copied to dest_dir and counted as 'copied'."""
    src = tmp_path / "kick.wav"
    src.write_bytes(b"RIFF")
    dest = tmp_path / "fl_export"

    from samplemind.integrations.filesystem import export_to_fl_studio

    result = export_to_fl_studio([src], dest_dir=dest)
    assert result["copied"] == 1
    assert result["skipped"] == 0
    assert result["targets"] == 1
    assert (dest / "kick.wav").exists()


def test_export_to_fl_studio_skips_missing_file(tmp_path: Path):
    """A path that doesn't exist on disk is silently skipped (not counted)."""
    ghost = tmp_path / "missing.wav"  # never created
    dest = tmp_path / "fl_export"

    from samplemind.integrations.filesystem import export_to_fl_studio

    result = export_to_fl_studio([ghost], dest_dir=dest)
    assert result["copied"] == 0
    assert result["skipped"] == 0


def test_export_to_fl_studio_skips_uptodate_copy(tmp_path: Path):
    """A file whose destination copy is newer than the source is skipped."""
    src = tmp_path / "kick.wav"
    src.write_bytes(b"RIFF")
    dest = tmp_path / "fl_export"
    dest.mkdir()

    # Pre-copy the file
    import shutil
    import time
    shutil.copy2(src, dest / "kick.wav")
    # Touch destination to be strictly newer
    time.sleep(0.01)
    future_mtime = src.stat().st_mtime + 10
    (dest / "kick.wav").touch()
    import os
    os.utime(dest / "kick.wav", (future_mtime, future_mtime))

    from samplemind.integrations.filesystem import export_to_fl_studio

    result = export_to_fl_studio([src], dest_dir=dest)
    assert result["copied"] == 0
    assert result["skipped"] == 1


def test_export_to_fl_studio_no_fl_raises(tmp_path: Path):
    """When no FL Studio is installed and no dest_dir given, RuntimeError is raised."""
    from samplemind.integrations.filesystem import export_to_fl_studio
    from samplemind.integrations import paths

    with patch.object(paths, "get_fl_studio_paths", return_value=[]):
        with pytest.raises(RuntimeError, match="No FL Studio installation"):
            export_to_fl_studio([tmp_path / "kick.wav"])
