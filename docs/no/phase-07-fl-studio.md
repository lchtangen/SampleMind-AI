# Fase 7 — FL Studio-integrasjon (macOS og Windows)

> Koble SampleMind til FL Studio ved hjelp av filsystem-eksport, AppleScript-automatisering,
> virtuell MIDI og clipboard — fra enklest til mest integrert.

---

## Forutsetninger

- Fase 1–6 fullført
- FL Studio installert på macOS (testet) eller Windows
- macOS: AppleScript-tilgang til FL Studio

---

## Mål etter denne fasen

- `samplemind export --fl-studio` skriver en FL Studio-kompatibel mappestruktur
- Python-modul for AppleScript-automatisering
- Clipboard-kopiering av sample-stier
- Virtuell MIDI-port for BPM/key-sending
- Forståelse av FL Studio's filsystem-layout på macOS og Windows

---

## 1. FL Studio-stier

### macOS

```
~/Documents/Image-Line/FL Studio/
├── Projects/                   ← .flp-prosjektfiler
│   └── MittProsjekt.flp
├── Data/
│   └── Patches/
│       └── Samples/            ← FL Studio's interne sample-mappe
│           └── SampleMind/     ← Vi lager denne
└── Presets/

~/Music/                        ← Anbefalt sted for egne sample-biblioteker
└── SampleMind/
    ├── Drums/
    ├── Bass/
    └── Pads/
```

### Windows

```
C:\Users\BrukernAvn\Documents\Image-Line\FL Studio\
├── Projects\
├── Data\
│   └── Patches\
│       └── Samples\
└── Presets\

# Typisk egendefinert bibliotekmappe:
C:\Users\BrukernAvn\Music\SampleMind\
```

### Python-konstanter

```python
# filename: src/samplemind/integrations/paths.py

import sys
from pathlib import Path

def get_fl_studio_samples_dir() -> Path:
    """
    Returner standard FL Studio sample-mappe basert på plattform.
    Brukeren kan overstyre dette med en miljøvariabel.
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

## 2. Nivå 1 — Filsystem-integrasjon

Det enkleste: skriv samples til en mappe FL Studio kan lese direkte.

```python
# filename: src/samplemind/integrations/filesystem.py

import shutil
from pathlib import Path
from samplemind.core.models.sample import Sample
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.integrations.paths import get_fl_studio_samples_dir


def export_to_fl_studio(
    samples: list[Sample],
    target_dir: Path | None = None,
    organize_by: str = "instrument",  # "instrument", "mood", "genre"
) -> dict[str, int]:
    """
    Eksporter samples til en FL Studio-kompatibel mappestruktur.

    Returnerer: {"eksportert": N, "hoppet_over": M}

    FL Studio indekserer mapper automatisk i sin fil-browser,
    så vi trenger bare å kopiere filene til riktig sted.
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

        # Bestem undermappe basert på organiserings-strategi
        if organize_by == "instrument" and sample.instrument:
            subfolder = sample.instrument.capitalize()  # "kick" → "Kick"
        elif organize_by == "mood" and sample.mood:
            subfolder = sample.mood.capitalize()
        elif organize_by == "genre" and sample.genre:
            subfolder = sample.genre.capitalize()
        else:
            subfolder = "Misc"

        # Lag destinasjonsmappe og kopier filen
        dest_dir = target_dir / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Lag et beskrivende filnavn: "kick_128bpm_Cmaj.wav"
        bpm_str = f"_{int(sample.bpm)}bpm" if sample.bpm else ""
        key_str = f"_{sample.key.replace(' ', '')}" if sample.key else ""
        new_name = f"{src.stem}{bpm_str}{key_str}{src.suffix}"

        dest = dest_dir / new_name
        if not dest.exists():
            shutil.copy2(str(src), str(dest))
            exported += 1
        else:
            skipped += 1

    return {"eksportert": exported, "hoppet_over": skipped}


def get_export_tree(target_dir: Path | None = None) -> list[str]:
    """Vis mappestrukturen som vil bli opprettet."""
    if target_dir is None:
        target_dir = get_fl_studio_samples_dir() / "SampleMind"
    return [str(target_dir / cat) for cat in
            ["Kick", "Snare", "Hihat", "Bass", "Pad", "Lead", "Loop", "SFX"]]
```

CLI-kommando for eksport:

```python
# filename: src/samplemind/cli/commands/export.py

import typer
from pathlib import Path
from rich.console import Console
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.integrations.filesystem import export_to_fl_studio

console = Console()


def export_cmd(
    target: Path = typer.Option(None, "--target", "-t", help="Mål-mappe (standard: FL Studio sin)"),
    organize: str = typer.Option("instrument", "--organize",
                                  help="Organiser etter: instrument, mood, genre"),
    energy: str = typer.Option(None, "--energy", help="Filtrer etter energinivå"),
):
    """Eksporter samples til FL Studio sin sample-browser."""
    samples = SampleRepository.search(energy=energy)

    if not samples:
        console.print("[yellow]Ingen samples å eksportere.[/yellow]")
        raise typer.Exit(0)

    console.print(f"Eksporterer {len(samples)} samples til FL Studio...")
    result = export_to_fl_studio(samples, target_dir=target, organize_by=organize)

    console.print(f"[green]Ferdig:[/green] {result['eksportert']} eksportert, "
                  f"{result['hoppet_over']} hoppet over.")
    console.print("\nÅpne FL Studio → File Browser → Finn SampleMind-mappen")
```

---

## 3. Nivå 2 — Clipboard-kopiering

Kopierer sample-stien til utklippstavlen. Brukeren kan deretter lime inn i FL Studio:

```python
# filename: src/samplemind/integrations/clipboard.py

import sys
import subprocess
from pathlib import Path
from samplemind.core.models.sample import Sample


def copy_sample_path(sample: Sample) -> bool:
    """
    Kopier sample-stien til systemets utklippstavle.

    macOS:   bruker pbcopy
    Windows: bruker clip
    Linux:   bruker xclip eller xsel
    """
    path = str(Path(sample.path))

    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=path.encode(), check=True)
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=path.encode("utf-16"), check=True)
        else:
            # Linux: prøv xclip, fall tilbake til xsel
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
    Lag en lesbar metadatastreng som kan limes inn i FL Studio-notater.
    Eksempel: "kick_128.wav | 128.0 BPM | C maj | kick | high energy"
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

## 4. Nivå 3 — AppleScript-automatisering

AppleScript lar Python/Rust styre macOS-apper programmatisk.

```python
# filename: src/samplemind/integrations/applescript.py

import subprocess
import sys


def _run_applescript(script: str) -> tuple[bool, str]:
    """
    Kjør et AppleScript og returner (suksess, output).
    Fungerer kun på macOS.
    """
    if sys.platform != "darwin":
        return False, "AppleScript er kun tilgjengelig på macOS"

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout.strip()


def focus_fl_studio() -> bool:
    """Bring FL Studio til forgrunnen."""
    ok, _ = _run_applescript('tell application "FL Studio" to activate')
    return ok


def is_fl_studio_running() -> bool:
    """Sjekk om FL Studio kjører."""
    ok, output = _run_applescript(
        'tell application "System Events" to '
        '(name of processes) contains "FL Studio"'
    )
    return ok and output.lower() == "true"


def open_sample_browser() -> bool:
    """
    Åpne sample-browser i FL Studio (F8-tastetrykk).
    OBS: Krever at FL Studio er i forgrunnen.
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


def get_fl_studio_project_path() -> str | None:
    """
    Hent stien til det aktive FL Studio-prosjektet.
    Returnerer None hvis FL Studio ikke kjører eller ingen prosjekt er åpent.
    """
    script = """
    tell application "System Events"
        tell process "FL Studio"
            set windowTitle to name of front window
        end tell
    end tell
    return windowTitle
    """
    ok, title = _run_applescript(script)
    if ok and title:
        return title
    return None
```

Tilsvarende Rust-versjon (for Tauri-appen):

```rust
// filename: app/src-tauri/src/commands/applescript.rs

use std::process::Command;

/// Kjør AppleScript fra Rust (macOS only)
#[tauri::command]
#[cfg(target_os = "macos")]
pub async fn focus_fl_studio() -> Result<(), String> {
    Command::new("osascript")
        .args(["-e", r#"tell application "FL Studio" to activate"#])
        .output()
        .map(|_| ())
        .map_err(|e| e.to_string())
}

/// No-op på Windows
#[tauri::command]
#[cfg(not(target_os = "macos"))]
pub async fn focus_fl_studio() -> Result<(), String> {
    Err("AppleScript er kun tilgjengelig på macOS".to_string())
}
```

---

## 5. Nivå 4 — Virtuell MIDI

Virtuell MIDI lar SampleMind sende BPM og toneart til FL Studio som MIDI-meldinger.

### macOS-oppsett (IAC Driver)

```
1. Åpne "Audio MIDI Setup" (finn i Programmer/Verktøy)
2. Gå til "Vindu" → "Vis MIDI-studio"
3. Dobbeltklikk "IAC Driver"
4. Aktiver "Enheten er online"
5. Legg til en port (f.eks. "SampleMind")
6. I FL Studio: MIDI-innstillinger → Aktiver IAC Driver → SampleMind
```

```python
# filename: src/samplemind/integrations/midi.py
# Krev: uv add python-rtmidi

import rtmidi

from samplemind.core.models.sample import Sample


# MIDI CC-numre vi bruker for å sende metadata
CC_BPM_COARSE = 14    # BPM heltall (0-127 = 0-127 BPM)
CC_BPM_FINE   = 15    # BPM desimal (0-127 = 0.0-0.99)
CC_KEY_ROOT   = 16    # Rotnotenummer (0=C, 1=C#, ..., 11=B)
CC_KEY_MODE   = 17    # 0 = dur, 64 = moll


def create_virtual_midi_port() -> rtmidi.MidiOut:
    """
    Opprett en virtuell MIDI-utgangsport kalt 'SampleMind'.
    FL Studio kan koble seg til denne i MIDI-innstillingene.
    """
    midi_out = rtmidi.MidiOut()
    # Prøv å bruke eksisterende port, ellers opprett virtuell
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
    Send sample-metadata til FL Studio som MIDI CC-meldinger.
    FL Studio kan bruke disse til å justere prosjektets BPM og toneart.
    """
    # Send BPM (delt i grov og fin oppløsning for mer presisjon)
    if sample.bpm:
        bpm_int = min(127, int(sample.bpm))
        bpm_frac = int((sample.bpm - bpm_int) * 127)
        # MIDI CC format: [0xB0 | kanal, CC-nummer, verdi]
        port.send_message([0xB0, CC_BPM_COARSE, bpm_int])
        port.send_message([0xB0, CC_BPM_FINE, bpm_frac])

    # Send toneart
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

## 6. macOS Sandbox og entitlements

For at Tauri-appen skal få tilgang til filer og sende AppleScript:

```xml
<!-- filename: app/src-tauri/entitlements.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Brukeren velger filer — tilgang gis av OS (uten sandbox-brudd) -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>

    <!-- Tilgang til Musikk-mappen -->
    <key>com.apple.security.assets.music.read-write</key>
    <true/>

    <!-- Kjøre subprosesser (for AppleScript og Python-CLI) -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>

    <!-- Automatisering av andre apper (for AppleScript til FL Studio) -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
```

---

## 7. Fil-navngivningskonvensjoner

FL Studio's browser søker etter filnavn, så konsekvente navn er viktig:

```python
# filename: src/samplemind/integrations/naming.py

from samplemind.core.models.sample import Sample


def make_fl_filename(sample: Sample) -> str:
    """
    Lag et FL Studio-vennlig filnavn med metadata innebygd.

    Eksempel: "kick_trap_128bpm_Cmin_high.wav"
    FL Studios søk vil finne dette med: "kick", "128", "Cmin"
    """
    parts = []

    # Instrument (mest spesifikt)
    if sample.instrument and sample.instrument != "unknown":
        parts.append(sample.instrument)

    # Sjanger
    if sample.genre:
        parts.append(sample.genre.replace(" ", ""))

    # BPM
    if sample.bpm:
        parts.append(f"{int(sample.bpm)}bpm")

    # Toneart (uten mellomrom: "C min" → "Cmin")
    if sample.key:
        parts.append(sample.key.replace(" ", ""))

    # Energi (kunn hvis høy — skiller seg ut)
    if sample.energy == "high":
        parts.append("high")

    # Legg til original filnavn-stammen hvis ingen metadata
    if not parts:
        from pathlib import Path
        parts.append(Path(sample.path).stem)

    from pathlib import Path
    suffix = Path(sample.path).suffix
    return "_".join(parts) + suffix
```

---

## Migrasjonsnotater

- Disse er nye moduler — ingenting slettes
- `samplemind export` legges til i CLI `app.py` (Fase 4)
- `python-rtmidi` og `pyperclip` legges til i `pyproject.toml`

---

## Testsjekkliste

```bash
# Test filsystem-eksport
$ uv run samplemind export --target /tmp/fl-test/

# Bekreft at strukturen ble opprettet
$ ls /tmp/fl-test/SampleMind/

# Test clipboard-kopiering (macOS)
$ uv run python -c "
from samplemind.integrations.clipboard import copy_sample_path
# Krever et importert sample i databasen
"

# Test AppleScript (macOS, krever FL Studio)
$ uv run python -c "
from samplemind.integrations.applescript import is_fl_studio_running
print('FL Studio kjører:', is_fl_studio_running())
"
```

---

## Feilsøking

**AppleScript: `osascript: can't open input file`**
```bash
# Bekreft at macOS Accessibility er aktivert for terminalen:
# Systemvalg → Sikkerhet og personvern → Personvern → Tilgjengelighet
# Legg til: Terminal / VS Code / Tauri-appen
```

**MIDI-port ikke funnet**
```
Bekreft at IAC Driver er aktivert i Audio MIDI Setup (macOS).
Kjør:
$ python -c "import rtmidi; m = rtmidi.MidiOut(); print(m.get_ports())"
```

**FL Studio viser ikke nye filer i browser**
```
FL Studio skanner mapper ved oppstart. Trykk F5 i File Browser
for å tvinge en re-skanning av mappene.
```
