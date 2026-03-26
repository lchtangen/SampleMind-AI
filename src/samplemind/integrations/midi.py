"""MIDI CC and clock sync via python-rtmidi and IAC Driver.

Phase 7 — FL Studio Integration.
Sends MIDI CC messages to the IAC Driver (macOS) or loopMIDI (Windows) so
FL Studio can receive BPM values as MIDI CC data.  Also implements MIDI clock
output to sync FL Studio's transport to the currently-playing sample's BPM.

BPM encoding convention (14-bit, CC 14/46 on channel 1):
  MSB (bits 7-13): sent on CC 14  (0x0E)
  LSB (bits 0-6):  sent on CC 46  (0x2E)
  Range: 20 - 300 BPM (clamped)

MIDI clock: 24 pulses per quarter note (standard MIDI spec, per-bar sync)

Requires optional dependency: python-rtmidi
  Install with: uv add python-rtmidi  OR  uv sync --extra midi
"""

from __future__ import annotations

import threading
import time


def _get_rtmidi() -> object:  # type: ignore[return]
    """Import rtmidi or raise a helpful RuntimeError."""
    try:
        import rtmidi  # type: ignore[import-untyped]
        return rtmidi
    except ImportError as exc:
        raise RuntimeError(
            "python-rtmidi is required for MIDI output.  "
            "Install it with: uv add python-rtmidi"
        ) from exc


def list_midi_output_ports() -> list[str]:
    """Return the names of all available MIDI output ports.

    Returns:
        List of port name strings (may be empty if no MIDI hardware is present).

    Raises:
        RuntimeError: If python-rtmidi is not installed.
    """
    rtmidi = _get_rtmidi()
    midi_out = rtmidi.MidiOut()
    try:
        return midi_out.get_ports()
    finally:
        del midi_out


def _open_port_by_name(midi_out: object, port_name: str) -> None:
    """Open the first MIDI port whose name contains *port_name* (case-insensitive).

    Raises:
        RuntimeError: If no matching port is found, with the available port list.
    """
    ports: list[str] = midi_out.get_ports()  # type: ignore[attr-defined]
    for idx, name in enumerate(ports):
        if port_name.lower() in name.lower():
            midi_out.open_port(idx)  # type: ignore[attr-defined]
            return
    raise RuntimeError(
        f"MIDI port {port_name!r} not found.  "
        f"Available ports: {ports or ['(none)']}"
    )


def send_bpm_via_midi(
    bpm: float,
    port_name: str = "IAC Driver Bus 1",
) -> None:
    """Send BPM as 14-bit MIDI CC to an IAC Driver or loopMIDI port.

    Encodes the BPM value (clamped to 20-300) as a 14-bit value split across
    two Control Change messages on channel 1:
      CC 14 (0x0E) — most-significant 7 bits
      CC 46 (0x2E) — least-significant 7 bits

    FL Studio can receive these via a MIDI controller mapping.

    Args:
        bpm:       Beats per minute to send (clamped to 20-300).
        port_name: Partial name of the MIDI output port to open.

    Raises:
        RuntimeError: If python-rtmidi is not installed, or port is not found.
    """
    rtmidi = _get_rtmidi()
    bpm_int = max(20, min(300, round(bpm)))
    msb = (bpm_int >> 7) & 0x7F
    lsb = bpm_int & 0x7F

    midi_out = rtmidi.MidiOut()
    try:
        _open_port_by_name(midi_out, port_name)
        # CC on channel 1: status byte 0xB0 | channel (0)
        midi_out.send_message([0xB0, 0x0E, msb])   # CC 14 — MSB
        midi_out.send_message([0xB0, 0x2E, lsb])   # CC 46 — LSB
    finally:
        del midi_out


def send_midi_clock_pulse(
    port_name: str = "IAC Driver Bus 1",
    pulses: int = 24,
) -> None:
    """Send MIDI clock tick bytes (0xF8) to trigger one bar of sync.

    24 pulses = one quarter note at any BPM (per MIDI standard).
    Use this to manually nudge FL Studio's transport into sync.

    Args:
        port_name: Partial name of the MIDI output port to open.
        pulses:    Number of 0xF8 clock ticks to send (default: 24 = 1 beat).

    Raises:
        RuntimeError: If python-rtmidi is not installed, or port is not found.
    """
    rtmidi = _get_rtmidi()
    midi_out = rtmidi.MidiOut()
    try:
        _open_port_by_name(midi_out, port_name)
        for _ in range(pulses):
            midi_out.send_message([0xF8])  # MIDI clock tick
            time.sleep(0.001)  # 1 ms gap prevents buffer overflow
    finally:
        del midi_out


class MidiBpmSync:
    """Continuous MIDI clock sender (0xF8 pulses) running in a background thread.

    Sends MIDI Timing Clock bytes at the rate required for the current BPM:
        pulse_interval = 60.0 / (bpm * 24)

    Thread-safe BPM updates: calling update_bpm() sets _bpm_changed so the
    background sleep loop wakes immediately and recalculates the interval.

    Usage::

        sync = MidiBpmSync()
        sync.start(128.0, port_name="IAC Driver Bus 1")
        sync.update_bpm(140.0)   # mid-session tempo change
        sync.stop()              # blocks until thread exits
    """

    def __init__(self) -> None:
        self._bpm: float = 120.0
        self._port_name: str = "IAC Driver Bus 1"
        self._stop_event = threading.Event()
        self._bpm_changed = threading.Event()
        self._thread: threading.Thread | None = None
        self._midi_out: object | None = None

    def start(self, bpm: float, port_name: str = "IAC Driver Bus 1") -> None:
        """Start the background clock thread.

        No-op if already running — call stop() first to restart.

        Args:
            bpm:       Initial beats per minute (clamped to 20-300).
            port_name: Partial name of the MIDI output port.

        Raises:
            RuntimeError: If python-rtmidi is not installed, or port not found.
        """
        if self._thread is not None and self._thread.is_alive():
            return
        rtmidi = _get_rtmidi()
        self._bpm = max(20.0, min(300.0, bpm))
        self._port_name = port_name
        self._stop_event.clear()
        self._bpm_changed.clear()
        self._midi_out = rtmidi.MidiOut()
        _open_port_by_name(self._midi_out, port_name)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update_bpm(self, bpm: float) -> None:
        """Change the BPM while the clock is running.

        Thread-safe.  The new rate takes effect on the next pulse cycle.

        Args:
            bpm: New beats per minute (clamped to 20-300).
        """
        self._bpm = max(20.0, min(300.0, bpm))
        self._bpm_changed.set()

    def stop(self) -> None:
        """Stop the background clock thread and close the MIDI port.

        Blocks until the thread exits (at most one pulse interval + 2 s timeout).
        """
        self._stop_event.set()
        self._bpm_changed.set()  # wake the sleep loop immediately
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._midi_out is not None:
            del self._midi_out
            self._midi_out = None

    def _run(self) -> None:
        """Background loop: send one 0xF8 pulse, then sleep until the next beat."""
        while not self._stop_event.is_set():
            pulse_interval = 60.0 / (self._bpm * 24)
            self._bpm_changed.clear()
            if self._midi_out is not None:
                self._midi_out.send_message([0xF8])  # type: ignore[attr-defined]
            # Sleep for the pulse interval, waking early on BPM change or stop
            self._bpm_changed.wait(timeout=pulse_interval)
