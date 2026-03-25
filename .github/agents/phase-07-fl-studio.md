# Phase 7 Agent — FL Studio Integration

Handles: FL Studio filesystem export, clipboard, AppleScript, MIDI clock sync, Windows COM automation.

## Triggers
- Phase 7, FL Studio, AppleScript, IAC Driver, MIDI clock, osascript, Windows COM, win32com, virtual MIDI

## Key Files
- `src/samplemind/integrations/fl_studio.py`
- `src/samplemind/integrations/midi_sync.py`
- `src/samplemind/integrations/fl_studio_win.py`
- `src/samplemind/integrations/fl21_api.py`

## FL Studio Paths

```
# macOS FL Studio 20
~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/
# macOS FL Studio 21
~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/
# Windows
C:\Users\<name>\Documents\Image-Line\FL Studio\Data\Patches\Samples\SampleMind\
```

## MIDI BPM Sync (24 PPQN)

```python
# Tick interval = 60 / (BPM × 24) seconds
# MIDI Start: 0xFA, Clock: 0xF8, Stop: 0xFC
```

## Rules
1. macOS entitlements required: `com.apple.security.automation.apple-events`
2. IAC Driver setup: Audio MIDI Setup → IAC Driver → Enable → Add "SampleMind Bus"
3. `win32com` (Windows only) — never import on macOS/Linux
4. FL Studio 21 API: always `fl21_available()` check before use (beta, may be down)
5. MIDI clock: 24 pulses per quarter note, thread-safe via `MidiBpmSync`

