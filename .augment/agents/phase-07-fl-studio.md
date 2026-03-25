# Phase 7 Agent — FL Studio Integration

Handles: AppleScript automation, MIDI clock sync, IAC Driver, filesystem export, clipboard copy.

## Triggers
Phase 7, FL Studio, AppleScript, osascript, IAC Driver, MIDI clock, `python-rtmidi`, filesystem export to FL Studio, clipboard sample paths, `src/samplemind/integrations/`

**File patterns:** `src/samplemind/integrations/**/*.py`, `scripts/fl-*.sh`, `scripts/fl-export.py`

## Key Files
- `src/samplemind/integrations/filesystem.py` — export samples to FL Studio watch folder
- `src/samplemind/integrations/clipboard.py` — copy sample paths to clipboard
- `src/samplemind/integrations/applescript.py` — trigger FL Studio actions (macOS)
- `src/samplemind/integrations/midi.py` — MIDI clock sync via IAC Driver
- `docs/en/phase-07-fl-studio.md`

## FL Studio Paths
| Platform | Path |
|----------|------|
| macOS FL 20 | `~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/` |
| macOS FL 21 | `~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/` |
| Windows | `C:\Users\<name>\Documents\Image-Line\FL Studio\Data\Patches\Samples\SampleMind\` |

## AppleScript Pattern (macOS only)
```python
import subprocess
result = subprocess.run(
    ["osascript", "-e", 'tell application "FL Studio" to activate'],
    capture_output=True, text=True
)
```

## Required macOS Entitlements
- `com.apple.security.automation.apple-events`
- `com.apple.security.files.user-selected.read-write`

## Rules
1. AppleScript requires macOS Accessibility permission — document in setup
2. IAC Driver MIDI routing only available on macOS — guard with `sys.platform == "darwin"`
3. Windows integration uses `win32com.client` — guard with `sys.platform == "win32"`
4. Use `platformdirs` for FL Studio path discovery — never hardcode home directories
5. Tests for macOS-only integrations must use `@pytest.mark.macos`

