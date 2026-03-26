"""Copy sample file paths to the system clipboard.

Phase 7 — FL Studio Integration.
Writes the absolute path of one or more WAV files to the OS clipboard so the
user can paste them directly into FL Studio's Channel Rack or Playlist.

macOS: uses pbcopy
Windows: uses clip.exe  (UTF-16 LE for full Unicode support)
Linux: uses xclip (primary) or xsel (fallback)
"""

from __future__ import annotations

from pathlib import Path
import platform
import subprocess


def copy_paths_to_clipboard(paths: list[Path]) -> None:
    """Write one path per line to the OS clipboard.

    No-op when *paths* is empty.

    Args:
        paths: Absolute paths to write.

    Raises:
        RuntimeError: On Linux if neither ``xclip`` nor ``xsel`` is found in PATH.
        subprocess.CalledProcessError: If the clipboard command exits non-zero.
    """
    if not paths:
        return

    text = "\n".join(str(p) for p in paths)
    system = platform.system()

    if system == "Darwin":
        subprocess.run(["pbcopy"], input=text.encode(), check=True)  # noqa: S607

    elif system == "Windows":
        # clip.exe requires UTF-16 LE with BOM for proper Unicode handling
        subprocess.run(["clip"], input=text.encode("utf-16"), check=True)  # noqa: S607

    else:
        # Linux — try xclip first, then xsel
        for cmd, args in [
            ("xclip", ["-selection", "clipboard"]),
            ("xsel", ["--clipboard", "--input"]),
        ]:
            try:
                subprocess.run(  # noqa: S603
                    [cmd, *args],
                    input=text.encode(),
                    check=True,
                )
                return
            except FileNotFoundError:
                continue

        raise RuntimeError(
            "No clipboard utility found.  "
            "Install xclip (apt install xclip) or xsel (apt install xsel)."
        )
