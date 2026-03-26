"""Integration tests for Phase 7 — FL Studio integration modules.

All tests run on all platforms via monkeypatching of OS-level calls.
No real FL Studio, clipboard, MIDI hardware, or macOS required.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ── FL Studio path detection ───────────────────────────────────────────────────


def test_fl_paths_macos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On macOS with both FL versions installed, return two paths."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")

    # Mock home directory so we control which directories "exist"
    fake_home = tmp_path / "home"
    image_line = fake_home / "Documents" / "Image-Line"
    (image_line / "FL Studio").mkdir(parents=True)
    (image_line / "FL Studio 21").mkdir(parents=True)

    monkeypatch.setattr("samplemind.integrations.paths._image_line_root", lambda: image_line)

    from samplemind.integrations.paths import get_fl_studio_paths
    paths = get_fl_studio_paths()

    assert len(paths) == 2
    assert all("SampleMind" in str(p) for p in paths)
    assert any("FL Studio 21" in str(p) for p in paths)


def test_fl_paths_only_one_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only return paths for installed versions."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")

    fake_il = tmp_path / "Image-Line"
    (fake_il / "FL Studio").mkdir(parents=True)
    # FL Studio 21 NOT created

    monkeypatch.setattr("samplemind.integrations.paths._image_line_root", lambda: fake_il)

    from samplemind.integrations.paths import get_fl_studio_paths
    paths = get_fl_studio_paths()

    assert len(paths) == 1
    assert "FL Studio 21" not in str(paths[0])


def test_fl_paths_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Linux, always return an empty list."""
    monkeypatch.setattr("platform.system", lambda: "Linux")

    from samplemind.integrations.paths import get_fl_studio_paths
    assert get_fl_studio_paths() == []


def test_fl_paths_no_fl_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When FL Studio directories don't exist, return empty list."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("samplemind.integrations.paths._image_line_root", lambda: tmp_path)

    from samplemind.integrations.paths import get_fl_studio_paths
    assert get_fl_studio_paths() == []


# ── export_to_fl_studio ────────────────────────────────────────────────────────


def test_export_to_fl_studio_copies_files(tmp_path: Path, silent_wav: Path) -> None:
    """Files should be copied to the destination directory."""
    dest = tmp_path / "fl_export"
    from samplemind.integrations.filesystem import export_to_fl_studio

    result = export_to_fl_studio([silent_wav], dest_dir=dest)

    assert result["copied"] == 1
    assert result["skipped"] == 0
    assert result["targets"] == 1
    assert (dest / silent_wav.name).exists()


def test_export_skips_newer_files(tmp_path: Path, silent_wav: Path) -> None:
    """If destination is newer than source, the file is skipped."""
    import os

    dest = tmp_path / "fl_export"
    dest.mkdir()
    dst_file = dest / silent_wav.name
    dst_file.write_bytes(b"already there")

    # Make dst_file appear newer than silent_wav
    future_mtime = silent_wav.stat().st_mtime + 10.0
    os.utime(dst_file, (future_mtime, future_mtime))

    from samplemind.integrations.filesystem import export_to_fl_studio
    result = export_to_fl_studio([silent_wav], dest_dir=dest)

    assert result["skipped"] == 1
    assert result["copied"] == 0


def test_export_to_fl_studio_no_fl_installed(
    tmp_path: Path, silent_wav: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If no FL Studio is found and no dest_dir given, raise RuntimeError."""
    monkeypatch.setattr("platform.system", lambda: "Linux")

    from samplemind.integrations.filesystem import export_to_fl_studio
    with pytest.raises(RuntimeError, match="No FL Studio"):
        export_to_fl_studio([silent_wav])


# ── build_fl_filename ──────────────────────────────────────────────────────────


def test_build_fl_filename_full() -> None:
    from samplemind.integrations.filesystem import build_fl_filename
    name = build_fl_filename("kick", bpm=128.0, key="C# min", energy="high")
    assert name == "kick_128bpm_Cs_min_high.wav"


def test_build_fl_filename_missing_fields() -> None:
    from samplemind.integrations.filesystem import build_fl_filename
    name = build_fl_filename("pad")
    assert "unknown" in name
    assert name.endswith(".wav")


# ── clipboard ─────────────────────────────────────────────────────────────────


def test_copy_to_clipboard_empty() -> None:
    """Empty path list should not call any subprocess."""
    from samplemind.integrations.clipboard import copy_paths_to_clipboard
    with patch("subprocess.run") as mock_run:
        copy_paths_to_clipboard([])
    mock_run.assert_not_called()


def test_copy_to_clipboard_macos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On macOS, pbcopy is called with newline-joined paths."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")

    paths = [tmp_path / "kick.wav", tmp_path / "snare.wav"]
    expected_input = "\n".join(str(p) for p in paths).encode()

    with patch("subprocess.run") as mock_run:
        from samplemind.integrations.clipboard import copy_paths_to_clipboard
        copy_paths_to_clipboard(paths)

    mock_run.assert_called_once_with(["pbcopy"], input=expected_input, check=True)


def test_copy_to_clipboard_linux_xclip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On Linux, try xclip first."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    paths = [tmp_path / "loop.wav"]

    with patch("subprocess.run") as mock_run:

        # Force reimport to pick up monkeypatched platform.system
        import importlib

        import samplemind.integrations.clipboard as _clip_mod
        importlib.reload(_clip_mod)

        _clip_mod.copy_paths_to_clipboard(paths)

    assert mock_run.called
    cmd_used = mock_run.call_args[0][0]
    assert cmd_used[0] in ("xclip", "xsel")


def test_copy_to_clipboard_linux_no_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On Linux with no clipboard tool available, raise RuntimeError."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    paths = [tmp_path / "loop.wav"]

    with patch("subprocess.run", side_effect=FileNotFoundError):
        import importlib

        import samplemind.integrations.clipboard as _clip_mod
        importlib.reload(_clip_mod)

        with pytest.raises(RuntimeError, match="clipboard utility"):
            _clip_mod.copy_paths_to_clipboard(paths)


# ── applescript ───────────────────────────────────────────────────────────────


def test_applescript_raises_on_non_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    """All AppleScript functions must raise on non-macOS."""
    monkeypatch.setattr("platform.system", lambda: "Linux")

    from samplemind.integrations.applescript import (
        focus_fl_studio,
        is_fl_studio_running,
        run_applescript,
    )
    with pytest.raises(RuntimeError, match="macOS"):
        run_applescript("anything")
    with pytest.raises(RuntimeError, match="macOS"):
        focus_fl_studio()
    with pytest.raises(RuntimeError, match="macOS"):
        is_fl_studio_running()


def test_applescript_error_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-zero osascript exit code raises RuntimeError with the error text."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_result = MagicMock(returncode=1, stderr="execution error", stdout="")

    with patch("subprocess.run", return_value=fake_result):
        from samplemind.integrations.applescript import run_applescript
        with pytest.raises(RuntimeError, match="AppleScript error"):
            run_applescript("bad script")


def test_is_fl_studio_running_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_result = MagicMock(returncode=0, stdout="true", stderr="")

    with patch("subprocess.run", return_value=fake_result):
        from samplemind.integrations.applescript import is_fl_studio_running
        assert is_fl_studio_running() is True


def test_is_fl_studio_running_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_result = MagicMock(returncode=0, stdout="false", stderr="")

    with patch("subprocess.run", return_value=fake_result):
        from samplemind.integrations.applescript import is_fl_studio_running
        assert is_fl_studio_running() is False


# ── MIDI ──────────────────────────────────────────────────────────────────────


def test_midi_no_rtmidi_raises() -> None:
    """Missing python-rtmidi must raise RuntimeError with install hint."""
    with patch.dict("sys.modules", {"rtmidi": None}):
        import importlib

        from samplemind.integrations import midi as midi_mod
        importlib.reload(midi_mod)

        with pytest.raises(RuntimeError, match="python-rtmidi"):
            midi_mod.send_bpm_via_midi(128.0)


def test_midi_port_not_found_raises() -> None:
    """Requesting a port that doesn't exist raises RuntimeError with port list."""
    mock_rtmidi = MagicMock()
    mock_out = MagicMock()
    mock_out.get_ports.return_value = ["Some Other Port"]
    mock_rtmidi.MidiOut.return_value = mock_out

    with patch.dict("sys.modules", {"rtmidi": mock_rtmidi}):
        import importlib

        import samplemind.integrations.midi as midi_mod
        importlib.reload(midi_mod)

        with pytest.raises(RuntimeError, match="not found"):
            midi_mod.send_bpm_via_midi(128.0, port_name="IAC Driver Bus 1")


def test_bpm_encoding_128() -> None:
    """BPM=128 must encode as MSB=1, LSB=0 (128 = 0b10000000)."""
    mock_rtmidi = MagicMock()
    mock_out = MagicMock()
    mock_out.get_ports.return_value = ["IAC Driver Bus 1"]
    mock_rtmidi.MidiOut.return_value = mock_out

    with patch.dict("sys.modules", {"rtmidi": mock_rtmidi}):
        import importlib

        import samplemind.integrations.midi as midi_mod
        importlib.reload(midi_mod)

        midi_mod.send_bpm_via_midi(128.0, port_name="IAC Driver")

    calls = mock_out.send_message.call_args_list
    assert calls[0] == call([0xB0, 0x0E, 1])   # CC14=MSB=1
    assert calls[1] == call([0xB0, 0x2E, 0])   # CC46=LSB=0


def test_bpm_encoding_clamped() -> None:
    """BPM outside 20-300 range must be clamped before encoding."""
    mock_rtmidi = MagicMock()
    mock_out = MagicMock()
    mock_out.get_ports.return_value = ["IAC Driver Bus 1"]
    mock_rtmidi.MidiOut.return_value = mock_out

    with patch.dict("sys.modules", {"rtmidi": mock_rtmidi}):
        import importlib

        import samplemind.integrations.midi as midi_mod
        importlib.reload(midi_mod)

        # BPM=999 should clamp to 300 (0b10_0101100 → MSB=2, LSB=44)
        midi_mod.send_bpm_via_midi(999.0, port_name="IAC Driver")

    calls = mock_out.send_message.call_args_list
    msb = calls[0][0][0][2]
    lsb = calls[1][0][0][2]
    assert (msb << 7) | lsb == 300


# ── windows_com ───────────────────────────────────────────────────────────────


def test_windows_com_raises_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """All three public functions raise RuntimeError mentioning 'Windows' on Linux."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    import samplemind.integrations.windows_com as wcom

    with pytest.raises(RuntimeError, match="Windows"):
        wcom.focus_fl_studio_windows()
    with pytest.raises(RuntimeError, match="Windows"):
        wcom.open_samples_folder_windows()
    with pytest.raises(RuntimeError, match="Windows"):
        wcom.is_fl_studio_running_windows()


def test_focus_fl_studio_windows_no_pywin32(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing pywin32 raises RuntimeError with install hint."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    with patch.dict("sys.modules", {"win32com": None, "win32com.client": None}):
        import samplemind.integrations.windows_com as wcom
        with pytest.raises(RuntimeError, match="pywin32"):
            wcom.focus_fl_studio_windows()


def test_focus_fl_studio_windows_app_activate(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppActivate is called with 'FL Studio' and returns without error on True."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    mock_shell = MagicMock()
    mock_shell.AppActivate.return_value = True
    mock_client = MagicMock()
    mock_client.Dispatch.return_value = mock_shell
    mock_win32com = MagicMock()
    mock_win32com.client = mock_client

    with patch.dict("sys.modules", {"win32com": mock_win32com, "win32com.client": mock_client}):
        import samplemind.integrations.windows_com as wcom
        wcom.focus_fl_studio_windows()

    mock_shell.AppActivate.assert_called_once_with("FL Studio")


def test_focus_fl_studio_windows_not_running_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppActivate returning False (FL Studio not running) raises RuntimeError."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    mock_shell = MagicMock()
    mock_shell.AppActivate.return_value = False
    mock_client = MagicMock()
    mock_client.Dispatch.return_value = mock_shell
    mock_win32com = MagicMock()
    mock_win32com.client = mock_client

    with patch.dict("sys.modules", {"win32com": mock_win32com, "win32com.client": mock_client}):
        import samplemind.integrations.windows_com as wcom
        with pytest.raises(RuntimeError, match="not running"):
            wcom.focus_fl_studio_windows()


def test_is_fl_studio_running_windows_psutil(monkeypatch: pytest.MonkeyPatch) -> None:
    """psutil path returns True when 'FL Studio.exe' appears in the process list."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    mock_proc = MagicMock()
    mock_proc.name.return_value = "FL Studio.exe"
    mock_psutil = MagicMock()
    mock_psutil.process_iter.return_value = [mock_proc]

    with patch.dict("sys.modules", {"psutil": mock_psutil}):
        import samplemind.integrations.windows_com as wcom
        assert wcom.is_fl_studio_running_windows() is True


def test_is_fl_studio_running_windows_tasklist_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falls back to tasklist /FI when psutil is not available."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    fake_result = MagicMock(stdout="FL64.exe  PID 1234  ...", returncode=0)

    with patch.dict("sys.modules", {"psutil": None}):
        with patch("subprocess.run", return_value=fake_result):
            import samplemind.integrations.windows_com as wcom
            assert wcom.is_fl_studio_running_windows() is True


# ── MidiBpmSync ───────────────────────────────────────────────────────────────


def test_midi_bpm_sync_start_and_stop() -> None:
    """start() spawns a thread and sends 0xF8 pulses; stop() joins the thread."""
    import time

    mock_rtmidi = MagicMock()
    mock_out = MagicMock()
    mock_out.get_ports.return_value = ["IAC Driver Bus 1"]
    mock_rtmidi.MidiOut.return_value = mock_out

    with patch.dict("sys.modules", {"rtmidi": mock_rtmidi}):
        import importlib

        import samplemind.integrations.midi as midi_mod

        importlib.reload(midi_mod)

        sync = midi_mod.MidiBpmSync()
        sync.start(120.0, port_name="IAC Driver")
        assert sync._thread is not None
        assert sync._thread.is_alive()
        # 120 BPM × 24 PPQ → 20.8 ms/pulse; 60 ms gives ≥2 pulses
        time.sleep(0.06)
        sync.stop()
        assert sync._thread is None

    mock_out.send_message.assert_any_call([0xF8])


def test_midi_bpm_sync_update_bpm() -> None:
    """update_bpm() clamps values and wakes the sleep loop immediately."""
    import time

    mock_rtmidi = MagicMock()
    mock_out = MagicMock()
    mock_out.get_ports.return_value = ["IAC Driver Bus 1"]
    mock_rtmidi.MidiOut.return_value = mock_out

    with patch.dict("sys.modules", {"rtmidi": mock_rtmidi}):
        import importlib

        import samplemind.integrations.midi as midi_mod

        importlib.reload(midi_mod)

        sync = midi_mod.MidiBpmSync()
        sync.start(120.0, port_name="IAC Driver")
        sync.update_bpm(999.0)
        assert sync._bpm == 300.0
        sync.update_bpm(1.0)
        assert sync._bpm == 20.0
        time.sleep(0.03)
        sync.stop()


def test_midi_bpm_sync_start_noop_if_running() -> None:
    """Calling start() a second time does not replace the running thread."""
    import time

    mock_rtmidi = MagicMock()
    mock_out = MagicMock()
    mock_out.get_ports.return_value = ["IAC Driver Bus 1"]
    mock_rtmidi.MidiOut.return_value = mock_out

    with patch.dict("sys.modules", {"rtmidi": mock_rtmidi}):
        import importlib

        import samplemind.integrations.midi as midi_mod

        importlib.reload(midi_mod)

        sync = midi_mod.MidiBpmSync()
        sync.start(120.0, port_name="IAC Driver")
        first_thread = sync._thread
        sync.start(140.0, port_name="IAC Driver")  # noop
        assert sync._thread is first_thread          # same thread object
        time.sleep(0.03)
        sync.stop()
