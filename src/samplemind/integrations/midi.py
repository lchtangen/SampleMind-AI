"""MIDI CC and clock sync via python-rtmidi and IAC Driver.

Phase 7 — FL Studio Integration.
Sends MIDI CC messages to the IAC Driver (macOS) or loopMIDI (Windows) so
FL Studio can receive BPM, key, and energy values as MIDI CC data.
Also implements MIDI clock output to sync FL Studio's transport to the
currently-playing sample's BPM.

Requires optional dependency: python-rtmidi (uv sync --extra midi)
"""
# TODO: implement in Phase 7 — FL Studio Integration
