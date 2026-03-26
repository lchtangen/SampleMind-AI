"""Windows COM automation for FL Studio via pywin32.

Phase 7 — FL Studio Integration.
Uses win32com.client to automate FL Studio on Windows — bringing the window
to focus, opening the SampleMind samples folder, and detecting if FL Studio
is currently running.

Requires: pywin32>=306  (Windows only; guarded by _require_windows())
Install:  uv sync --extra windows
"""

from __future__ import annotations

import platform
import subprocess


def _require_windows() -> None:
    """Raise RuntimeError on non-Windows platforms."""
    if platform.system() != "Windows":
        raise RuntimeError(
            f"Windows COM automation requires Windows; "
            f"current platform is {platform.system()!r}"
        )


def focus_fl_studio_windows() -> None:
    """Bring FL Studio to the foreground on Windows via WScript.Shell.AppActivate.

    Raises:
        RuntimeError: On non-Windows, if pywin32 is not installed, or if
                      FL Studio is not currently running.
    """
    _require_windows()
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required for Windows COM automation.  "
            "Install it with: uv sync --extra windows"
        ) from exc
    shell = win32com.client.Dispatch("WScript.Shell")
    result: bool = shell.AppActivate("FL Studio")
    if not result:
        raise RuntimeError("FL Studio is not running or could not be focused.")


def open_samples_folder_windows(path: str | None = None) -> None:
    """Open the FL Studio SampleMind folder in Windows Explorer.

    Args:
        path: Override the folder path.  If None, auto-detects the first
              FL Studio installation via get_fl_studio_paths().

    Raises:
        RuntimeError: On non-Windows, or if no FL Studio installation is found
                      and no path override is given.
    """
    _require_windows()
    if path is None:
        from samplemind.integrations.paths import get_fl_studio_paths

        paths = get_fl_studio_paths()
        if not paths:
            raise RuntimeError(
                "No FL Studio installation detected on Windows.  "
                "Pass path explicitly or install FL Studio."
            )
        target = str(paths[0])
    else:
        target = path
    # check=False because explorer.exe always returns exit-code 1, even on success
    subprocess.run(["explorer", target], check=False)  # noqa: S603 S607


def is_fl_studio_running_windows() -> bool:
    """Return True if an FL Studio process is currently running on Windows.

    Prefers psutil for accuracy; falls back to ``tasklist /FI`` if psutil is
    not installed.

    Raises:
        RuntimeError: On non-Windows.
    """
    _require_windows()
    try:
        import psutil  # type: ignore[import-untyped]

        return any(
            "fl studio" in p.name().lower() for p in psutil.process_iter(["name"])
        )
    except ImportError:
        pass
    # Fallback: FL Studio 64-bit process is named FL64.exe
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq FL64.exe"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return "FL64.exe" in result.stdout
