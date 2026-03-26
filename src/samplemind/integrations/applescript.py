"""macOS AppleScript automation for FL Studio.

Phase 7 — FL Studio Integration.
Uses osascript to bring FL Studio to the foreground and query whether it is
running — automating the focus workflow before exporting samples.

All functions raise RuntimeError on non-macOS platforms.
Requires entitlement: com.apple.security.automation.apple-events
"""

from __future__ import annotations

import platform
import subprocess


def _require_macos() -> None:
    if platform.system() != "Darwin":
        raise RuntimeError(
            f"AppleScript requires macOS; current platform is {platform.system()!r}"
        )


def run_applescript(script: str) -> str:
    """Execute an AppleScript one-liner via ``osascript -e`` and return stdout.

    Args:
        script: Single AppleScript expression string.

    Returns:
        Stripped stdout from osascript.

    Raises:
        RuntimeError: On non-macOS or if osascript returns a non-zero exit code.
    """
    _require_macos()
    result = subprocess.run(  # noqa: S603
        ["osascript", "-e", script],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"AppleScript error (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def focus_fl_studio() -> None:
    """Bring FL Studio to the foreground using AppleScript.

    Raises:
        RuntimeError: On non-macOS or if FL Studio is not running.
    """
    run_applescript('tell application "FL Studio" to activate')


def is_fl_studio_running() -> bool:
    """Return True if FL Studio is currently running.

    Queries System Events for the process list.

    Raises:
        RuntimeError: On non-macOS.
    """
    _require_macos()
    script = (
        'tell application "System Events" '
        'to (name of processes) contains "FL Studio"'
    )
    result = run_applescript(script)
    return result.lower() == "true"
