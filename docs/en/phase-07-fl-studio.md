# Phase 7 — FL Studio Integration (macOS and Windows)

> Connect SampleMind to FL Studio using filesystem export, AppleScript automation,
> virtual MIDI, and clipboard — from simplest to most integrated.

---

## Prerequisites

- Phases 1–6 complete
- FL Studio installed on macOS (tested) or Windows
- macOS: AppleScript access to FL Studio

---

## Goal State

- `samplemind export --fl-studio` writes an FL Studio-compatible folder structure
- Python module for AppleScript automation
- Clipboard copying of sample paths
- Virtual MIDI port for sending BPM/key
- Understanding of FL Studio's filesystem layout on macOS and Windows

---

## 1. FL Studio Paths

### macOS

```
~/Documents/Image-Line/FL Studio/
├── Projects/                   ← .flp project files
│   └── MyProject.flp
├── Data/
│   └── Patches/
│       └── Samples/            ← FL Studio's internal sample folder
│           └── SampleMind/     ← We create this
└── Presets/

~/Music/                        ← Recommended location for own sample libraries
└── SampleMind/
    ├── Drums/
    ├── Bass/
    └── Pads/
```

### Windows

```
C:\Users\YourName\Documents\Image-Line\FL Studio\
├── Projects\
├── Data\
│   └── Patches\
│       └── Samples\
└── Presets\

# Typical custom library folder:
C:\Users\YourName\Music\SampleMind\
```

### Python Constants

```python
# filename: src/samplemind/integrations/paths.py

import sys
from pathlib import Path

def get_fl_studio_samples_dir() -> Path:
    """
    Return standard FL Studio sample folder based on platform.
    User can override with an environment variable.
    """
    import os
    if custom := os.environ.get("SAMPLEMIND_FL_DIR"):
        return Path(custom)

    if sys.platform == "darwin":  # macOS
        return (
            Path.home()
            / "Documents"
            / "Image-Line"
            / "FL Studio"
            / "Data"
            / "Patches"
            / "Samples"
        )
    elif sys.platform == "win32":  # Windows
        return (
            Path.home()
            / "Documents"
            / "Image-Line"
            / "FL Studio"
            / "Data"
            / "Patches"
            / "Samples"
        )
    else:  # Linux (Wine)
        return Path.home() / ".wine" / "drive_c" / "Users" / "user" / "Documents" / \
               "Image-Line" / "FL Studio" / "Data" / "Patches" / "Samples"
```

---

## 2. Level 1 — Filesystem Integration

The simplest approach: write samples to a folder FL Studio can read directly.

```python
# filename: src/samplemind/integrations/filesystem.py

import shutil
from pathlib import Path
from samplemind.data.repository import SampleRepository
from samplemind.models import Sample
from samplemind.integrations.paths import get_fl_studio_samples_dir


def export_to_fl_studio(
    samples: list[Sample],
    target_dir: Path | None = None,
    organize_by: str = "instrument",  # "instrument", "mood", "genre"
) -> dict[str, int]:
    """
    Export samples to an FL Studio-compatible folder structure.

    Returns: {"exported": N, "skipped": M}

    FL Studio automatically indexes folders in its file browser,
    so we just need to copy files to the right location.
    """
    if target_dir is None:
        target_dir = get_fl_studio_samples_dir() / "SampleMind"

    exported = 0
    skipped = 0

    for sample in samples:
        src = Path(sample.path)
        if not src.exists():
            skipped += 1
            continue

        # Determine subfolder based on organisation strategy
        if organize_by == "instrument" and sample.instrument:
            subfolder = sample.instrument.capitalize()  # "kick" → "Kick"
        elif organize_by == "mood" and sample.mood:
            subfolder = sample.mood.capitalize()
        elif organize_by == "genre" and sample.genre:
            subfolder = sample.genre.capitalize()
        else:
            subfolder = "Misc"

        dest_dir = target_dir / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Create a descriptive filename: "kick_128bpm_Cmaj.wav"
        bpm_str = f"_{int(sample.bpm)}bpm" if sample.bpm else ""
        key_str = f"_{sample.key.replace(' ', '')}" if sample.key else ""
        new_name = f"{src.stem}{bpm_str}{key_str}{src.suffix}"

        dest = dest_dir / new_name
        if not dest.exists():
            shutil.copy2(str(src), str(dest))
            exported += 1
        else:
            skipped += 1

    return {"exported": exported, "skipped": skipped}
```

CLI command for export:

```python
# filename: src/samplemind/cli/commands/export.py

import typer
from pathlib import Path
from rich.console import Console
from samplemind.data.repository import SampleRepository
from samplemind.integrations.filesystem import export_to_fl_studio

console = Console()


def export_cmd(
    target: Path = typer.Option(None, "--target", "-t", help="Target folder (default: FL Studio's)"),
    organize: str = typer.Option("instrument", "--organize",
                                  help="Organise by: instrument, mood, genre"),
    energy: str = typer.Option(None, "--energy", help="Filter by energy level"),
):
    """Export samples to FL Studio's sample browser."""
    repo = SampleRepository()
    samples = repo.search(energy=energy)

    if not samples:
        console.print("[yellow]No samples to export.[/yellow]")
        raise typer.Exit(0)

    console.print(f"Exporting {len(samples)} samples to FL Studio...")
    result = export_to_fl_studio(samples, target_dir=target, organize_by=organize)

    console.print(f"[green]Done:[/green] {result['exported']} exported, "
                  f"{result['skipped']} skipped.")
    console.print("\nOpen FL Studio → File Browser → Find the SampleMind folder")
```

---

## 3. Level 2 — Clipboard Copying

Copies the sample path to the clipboard. The user can then paste into FL Studio:

```python
# filename: src/samplemind/integrations/clipboard.py

import sys
import subprocess
from pathlib import Path
from samplemind.models import Sample


def copy_sample_path(sample: Sample) -> bool:
    """
    Copy the sample path to the system clipboard.

    macOS:   uses pbcopy
    Windows: uses clip
    Linux:   uses xclip or xsel
    """
    path = str(Path(sample.path))

    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=path.encode(), check=True)
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=path.encode("utf-16"), check=True)
        else:
            try:
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=path.encode(), check=True)
            except FileNotFoundError:
                subprocess.run(["xsel", "--clipboard", "--input"],
                               input=path.encode(), check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def copy_metadata_string(sample: Sample) -> str:
    """
    Build a readable metadata string that can be pasted into FL Studio notes.
    Example: "kick_128.wav | 128.0 BPM | C maj | kick | high energy"
    """
    parts = [sample.filename]
    if sample.bpm:
        parts.append(f"{sample.bpm:.1f} BPM")
    if sample.key:
        parts.append(sample.key)
    if sample.instrument:
        parts.append(sample.instrument)
    if sample.energy:
        parts.append(f"{sample.energy} energy")
    return " | ".join(parts)
```

---

## 4. Level 3 — AppleScript Automation

AppleScript lets Python/Rust control macOS apps programmatically.

```python
# filename: src/samplemind/integrations/applescript.py

import subprocess
import sys


def _run_applescript(script: str) -> tuple[bool, str]:
    """
    Run an AppleScript and return (success, output).
    Works only on macOS.
    """
    if sys.platform != "darwin":
        return False, "AppleScript is only available on macOS"

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout.strip()


def focus_fl_studio() -> bool:
    """Bring FL Studio to the foreground."""
    ok, _ = _run_applescript('tell application "FL Studio" to activate')
    return ok


def is_fl_studio_running() -> bool:
    """Check if FL Studio is running."""
    ok, output = _run_applescript(
        'tell application "System Events" to '
        '(name of processes) contains "FL Studio"'
    )
    return ok and output.lower() == "true"


def open_sample_browser() -> bool:
    """
    Open the sample browser in FL Studio (F8 keystroke).
    NOTE: Requires FL Studio to be in the foreground.
    """
    script = """
    tell application "FL Studio" to activate
    delay 0.3
    tell application "System Events"
        tell process "FL Studio"
            key code 98  -- F8
        end tell
    end tell
    """
    ok, _ = _run_applescript(script)
    return ok
```

Rust equivalent (for the Tauri app):

```rust
// filename: app/src-tauri/src/commands/applescript.rs

use std::process::Command;

/// Run AppleScript from Rust (macOS only)
#[tauri::command]
#[cfg(target_os = "macos")]
pub async fn focus_fl_studio() -> Result<(), String> {
    Command::new("osascript")
        .args(["-e", r#"tell application "FL Studio" to activate"#])
        .output()
        .map(|_| ())
        .map_err(|e| e.to_string())
}

/// No-op on Windows/Linux
#[tauri::command]
#[cfg(not(target_os = "macos"))]
pub async fn focus_fl_studio() -> Result<(), String> {
    Err("AppleScript is only available on macOS".to_string())
}
```

---

## 5. Level 4 — Virtual MIDI

Virtual MIDI lets SampleMind send BPM and key to FL Studio as MIDI messages.

### macOS Setup (IAC Driver)

```
1. Open "Audio MIDI Setup" (find in Applications/Utilities)
2. Go to "Window" → "Show MIDI Studio"
3. Double-click "IAC Driver"
4. Enable "Device is online"
5. Add a port (e.g. "SampleMind")
6. In FL Studio: MIDI Settings → Enable IAC Driver → SampleMind
```

```python
# filename: src/samplemind/integrations/midi.py
# Requires: uv add python-rtmidi

import rtmidi
from samplemind.models import Sample

# MIDI CC numbers we use to send metadata
CC_BPM_COARSE = 14    # BPM integer (0-127 = 0-127 BPM)
CC_BPM_FINE   = 15    # BPM decimal (0-127 = 0.0-0.99)
CC_KEY_ROOT   = 16    # Root note number (0=C, 1=C#, ..., 11=B)
CC_KEY_MODE   = 17    # 0 = major, 64 = minor


def create_virtual_midi_port() -> rtmidi.MidiOut:
    """
    Create a virtual MIDI output port called 'SampleMind'.
    FL Studio can connect to this in its MIDI settings.
    """
    midi_out = rtmidi.MidiOut()
    ports = midi_out.get_ports()
    samplemind_port = next(
        (i for i, p in enumerate(ports) if "SampleMind" in p or "IAC" in p), None
    )
    if samplemind_port is not None:
        midi_out.open_port(samplemind_port)
    else:
        midi_out.open_virtual_port("SampleMind")
    return midi_out


def send_sample_metadata(port: rtmidi.MidiOut, sample: Sample) -> None:
    """
    Send sample metadata to FL Studio as MIDI CC messages.
    FL Studio can use these to adjust the project's BPM and key.
    """
    if sample.bpm:
        bpm_int = min(127, int(sample.bpm))
        bpm_frac = int((sample.bpm - bpm_int) * 127)
        # MIDI CC format: [0xB0 | channel, CC number, value]
        port.send_message([0xB0, CC_BPM_COARSE, bpm_int])
        port.send_message([0xB0, CC_BPM_FINE, bpm_frac])

    if sample.key:
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        key_parts = sample.key.split()
        if len(key_parts) == 2:
            root_name, mode = key_parts
            if root_name in notes:
                root_cc = notes.index(root_name)
                mode_cc = 64 if "min" in mode else 0
                port.send_message([0xB0, CC_KEY_ROOT, root_cc])
                port.send_message([0xB0, CC_KEY_MODE, mode_cc])
```

---

## 6. macOS Sandbox and Entitlements

For the Tauri app to access files and send AppleScript:

```xml
<!-- filename: app/src-tauri/entitlements.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- User selects files — access granted by OS (no sandbox violation) -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>

    <!-- Access to Music folder -->
    <key>com.apple.security.assets.music.read-write</key>
    <true/>

    <!-- Run subprocesses (for AppleScript and Python CLI) -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>

    <!-- Automate other apps (for AppleScript to FL Studio) -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
```

---

## 7. File Naming Conventions

FL Studio's browser searches by filename, so consistent names matter:

```python
# filename: src/samplemind/integrations/naming.py

from samplemind.models import Sample


def make_fl_filename(sample: Sample) -> str:
    """
    Create an FL Studio-friendly filename with embedded metadata.

    Example: "kick_trap_128bpm_Cmin_high.wav"
    FL Studio search will find this with: "kick", "128", "Cmin"
    """
    parts = []

    if sample.instrument and sample.instrument != "unknown":
        parts.append(sample.instrument)

    if sample.genre:
        parts.append(sample.genre.replace(" ", ""))

    if sample.bpm:
        parts.append(f"{int(sample.bpm)}bpm")

    if sample.key:
        parts.append(sample.key.replace(" ", ""))  # "C min" → "Cmin"

    if sample.energy == "high":
        parts.append("high")

    if not parts:
        from pathlib import Path
        parts.append(Path(sample.path).stem)

    from pathlib import Path
    suffix = Path(sample.path).suffix
    return "_".join(parts) + suffix
```

---

## Migration Notes

- These are new modules — nothing is deleted
- `samplemind export` is added to CLI `app.py` (Phase 4)
- `python-rtmidi` and `pyperclip` are added to `pyproject.toml`

---

## Testing Checklist

```bash
# Test filesystem export
$ uv run samplemind export --target /tmp/fl-test/

# Confirm structure was created
$ ls /tmp/fl-test/SampleMind/

# Test clipboard copy (macOS)
$ uv run python -c "
from samplemind.integrations.clipboard import copy_sample_path
# Requires an imported sample in the database
"

# Test AppleScript (macOS, requires FL Studio)
$ uv run python -c "
from samplemind.integrations.applescript import is_fl_studio_running
print('FL Studio running:', is_fl_studio_running())
"
```

---

## Troubleshooting

**AppleScript: permission denied**
```
Enable Accessibility in System Preferences → Security & Privacy → Privacy → Accessibility.
Add: Terminal / VS Code / the Tauri app.
```

**MIDI port not found**
```bash
# Confirm IAC Driver is enabled in Audio MIDI Setup (macOS).
$ python -c "import rtmidi; m = rtmidi.MidiOut(); print(m.get_ports())"
```

**FL Studio doesn't show new files in browser**
```
FL Studio scans folders at startup. Press F5 in File Browser
to force a re-scan of the folders.
```

---

## 8. FL Studio 21 & Windows Integration (2026)

### FL Studio 21 Path Detection

FL Studio 21 uses a different directory suffix. Update path detection to handle both:

```python
# src/samplemind/integrations/paths.py
import platform
from pathlib import Path


def get_fl_studio_samples_dir() -> Path | None:
    """Detect the FL Studio Samples directory for the current OS and version."""
    system = platform.system()

    if system == "Darwin":  # macOS
        base = Path.home() / "Documents" / "Image-Line"
        # Try FL Studio 21 first, fall back to FL Studio 20
        for version_dir in ["FL Studio 21", "FL Studio"]:
            candidate = base / version_dir / "Data" / "Patches" / "Samples" / "SampleMind"
            if (base / version_dir).exists():
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate

    elif system == "Windows":
        base = Path.home() / "Documents" / "Image-Line"
        for version_dir in ["FL Studio 21", "FL Studio"]:
            candidate = base / version_dir / "Data" / "Patches" / "Samples" / "SampleMind"
            if (base / version_dir).exists():
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate

    return None
```

### macOS Paths Reference (FL Studio 20 and 21)

```
# FL Studio 20:
~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/
~/Library/Application Support/Image-Line/FL Studio/

# FL Studio 21:
~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/
~/Library/Application Support/Image-Line/FL Studio 21/

# Plugin locations (same for both versions):
~/Library/Audio/Plug-Ins/Components/SampleMind.component  ← AU
~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3            ← VST3
```

### Windows Paths Reference (FL Studio 20 and 21)

```
# FL Studio 20:
C:\Users\<name>\Documents\Image-Line\FL Studio\Data\Patches\Samples\SampleMind\
%APPDATA%\Image-Line\FL Studio\

# FL Studio 21:
C:\Users\<name>\Documents\Image-Line\FL Studio 21\Data\Patches\Samples\SampleMind\
%APPDATA%\Image-Line\FL Studio 21\

# Plugin locations:
C:\Program Files\Common Files\VST3\SampleMind.vst3
```

### Windows COM Automation

Alternative to AppleScript for Windows — use `win32com` (from `pywin32`):

```bash
uv add pywin32  # Windows only
```

```python
# src/samplemind/integrations/windows_com.py
import platform
from typing import TYPE_CHECKING


def focus_fl_studio_windows() -> None:
    """Bring FL Studio window to foreground on Windows using COM automation."""
    if platform.system() != "Windows":
        raise RuntimeError("Windows COM automation is only available on Windows")

    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    result = shell.AppActivate("FL Studio")
    if not result:
        raise RuntimeError("FL Studio is not running or could not be activated")


def open_fl_studio_sample_browser_windows() -> None:
    """Send F8 keystroke to FL Studio to open Sample Browser."""
    if platform.system() != "Windows":
        raise RuntimeError("Windows only")

    import win32com.client
    import win32con
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.AppActivate("FL Studio")
    shell.SendKeys("{F8}")
```

Guard Windows-only code in tests:
```python
import pytest, platform

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
def test_windows_com_focus():
    # ...
```

### MIDI Clock Sync via IAC Driver

Send BPM and key information via MIDI CC messages to FL Studio:

```python
# src/samplemind/integrations/midi.py
import rtmidi
from typing import Optional


def get_iac_port_index(name_hint: str = "SampleMind") -> Optional[int]:
    """Find the IAC Driver port index by name."""
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    for i, port in enumerate(ports):
        if name_hint.lower() in port.lower() or "iac" in port.lower():
            return i
    return None


def send_sample_metadata_midi(bpm: float, key_index: int, port: int = 0) -> None:
    """Send sample BPM and key as MIDI CC messages.

    CC 14 = BPM tens digit (e.g. 128 → CC14=12)
    CC 15 = BPM units digit (e.g. 128 → CC15=8)
    CC 16 = Key index (0=C, 1=C#, 2=D, ..., 11=B)

    FL Studio can map these CCs to tempo and other parameters.
    """
    midiout = rtmidi.MidiOut()
    available = midiout.get_ports()
    if not available:
        raise RuntimeError("No MIDI output ports available. Enable IAC Driver in Audio MIDI Setup.")

    midiout.open_port(port)
    channel = 0xB0  # CC on channel 1
    try:
        bpm_int = int(round(bpm))
        midiout.send_message([channel, 14, min(127, bpm_int // 10)])   # tens
        midiout.send_message([channel, 15, min(127, bpm_int % 10)])    # units
        midiout.send_message([channel, 16, min(127, key_index % 12)])  # key
    finally:
        midiout.close_port()
```

### IAC Driver Setup Guide (macOS)

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`)
2. Go to **Window → Show MIDI Studio** (or press ⌘2)
3. Double-click **IAC Driver**
4. Check **"Device is online"**
5. Under **Ports**, click **+** and name it **"SampleMind"**
6. Click **Apply**
7. In FL Studio: `Options → MIDI Settings → Input` — enable the IAC SampleMind port

Test the connection:
```bash
uv run python -c "
import rtmidi
m = rtmidi.MidiOut()
print('Available ports:', m.get_ports())
"
```

