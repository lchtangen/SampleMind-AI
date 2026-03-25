"""Analyze WAV samples without storing them in the library."""

import json
import os
import sys

from samplemind.analyzer.audio_analysis import analyze_file


def analyze_samples(folder: str, json_output: bool = False) -> None:
    """Analyze all WAV files in a folder and display results."""
    if not os.path.exists(folder):
        if json_output:
            print(json.dumps({"error": f"Folder not found: {folder}"}))
        else:
            print(f"❌ Folder not found: {folder}", file=sys.stderr)
        return

    wav_files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]
    if not wav_files:
        if json_output:
            print(json.dumps({"samples": []}))
        else:
            print("⚠️ No WAV files found.", file=sys.stderr)
        return

    results: list[dict] = []

    if not json_output:
        print(
            f"\n  {'Filename':<36} {'BPM':<7} {'Key':<10} {'Energy':<7} {'Mood':<12} {'Type'}",
            file=sys.stderr,
        )
        print("  " + "─" * 78, file=sys.stderr)

    for file in wav_files:
        file_path = os.path.join(folder, file)
        try:
            r = analyze_file(file_path)
            results.append({"filename": file, "path": os.path.abspath(file_path), **r})
            if not json_output:
                print(
                    f"  {file:<36} {str(r['bpm']):<7} {r['key']:<10} "
                    f"{r['energy']:<7} {r['mood']:<12} {r['instrument']}",
                    file=sys.stderr,
                )
        except Exception as e:  # noqa: BLE001
            if not json_output:
                print(f"  ❌ {file} — failed: {e}", file=sys.stderr)

    if json_output:
        print(json.dumps({"samples": results}))
