"""FL Studio installation path detection for macOS and Windows.

Phase 7 — FL Studio Integration.
Detects FL Studio 20 and FL Studio 21 data directories on the current platform
so samples can be exported to the correct Patches/Samples/SampleMind folder.

macOS paths:
  ~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/
  ~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/

Windows paths:
  %USERPROFILE%/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/
  %USERPROFILE%/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/
"""

from __future__ import annotations

import os
from pathlib import Path
import platform

# Sub-path inside the user's Documents/Image-Line/<FL version>/ tree
_SAMPLES_SUFFIX = Path("Data") / "Patches" / "Samples" / "SampleMind"

# FL Studio versions to probe
_FL_VERSIONS = ["FL Studio", "FL Studio 21"]


def _image_line_root() -> Path:
    """Return the platform-specific Image-Line documents directory."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Documents" / "Image-Line"
    elif system == "Windows":
        userprofile = os.environ.get("USERPROFILE", str(Path.home()))
        return Path(userprofile) / "Documents" / "Image-Line"
    else:
        return Path.home() / "Documents" / "Image-Line"  # fallback


def get_fl_studio_paths() -> list[Path]:
    """Return the SampleMind export paths for every detected FL Studio version.

    Checks whether the FL Studio parent directory actually exists (i.e., FL Studio
    is installed) before including the path.  Returns an empty list on Linux
    (FL Studio runs via WINE — path is not standardised).

    Returns:
        List of ``Patches/Samples/SampleMind/`` directories for each installed
        FL Studio version.  The directories are NOT created — callers should
        call ``mkdir(parents=True, exist_ok=True)`` before writing.
    """
    if platform.system() == "Linux":
        return []

    root = _image_line_root()
    found: list[Path] = []
    for version in _FL_VERSIONS:
        fl_dir = root / version
        if fl_dir.exists():
            found.append(fl_dir / _SAMPLES_SUFFIX)
    return found


def get_fl_studio_plugin_paths() -> dict[str, Path]:
    """Return the macOS plugin install locations for the SampleMind plugin.

    Returns a dict with keys "vst3" and "au" pointing to the canonical macOS
    plugin directories.

    Raises:
        RuntimeError: On non-macOS platforms (plugin paths are macOS-specific).
    """
    if platform.system() != "Darwin":
        raise RuntimeError(
            "FL Studio plugin paths are macOS-specific; "
            f"current platform is {platform.system()!r}"
        )
    plugin_root = Path.home() / "Library" / "Audio" / "Plug-Ins"
    return {
        "vst3": plugin_root / "VST3" / "SampleMind.vst3",
        "au": plugin_root / "Components" / "SampleMind.component",
    }
