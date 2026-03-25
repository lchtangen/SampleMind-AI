"""Import WAV samples into the library."""

import json
import os
import sys

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository


def import_samples(source: str, json_output: bool = False) -> None:
    """Import all WAV files from a folder and analyze + store them."""
    if not os.path.exists(source):
        if json_output:
            print(json.dumps({"error": f"Folder not found: {source}"}))
        else:
            print(f"❌ Folder not found: {source}", file=sys.stderr)
        return

    wav_files = [f for f in os.listdir(source) if f.lower().endswith(".wav")]
    if not wav_files:
        if json_output:
            print(json.dumps({"imported": 0, "errors": 0, "samples": []}))
        else:
            print("⚠️ No WAV files found in folder.", file=sys.stderr)
        return

    init_orm()

    imported = 0
    errors = 0
    results: list[dict] = []

    if not json_output:
        print(f"📂 Found {len(wav_files)} WAV file(s) in: {source}\n", file=sys.stderr)
        print(
            f"  {'Filename':<36} {'BPM':<7} {'Key':<10} {'Energy':<7} {'Mood':<12} {'Type'}",
            file=sys.stderr,
        )
        print("  " + "─" * 78, file=sys.stderr)

    for file in wav_files:
        file_path = os.path.abspath(os.path.join(source, file))
        try:
            r = analyze_file(file_path)
            data = SampleCreate(
                filename=file,
                path=file_path,
                bpm=r.get("bpm"),
                key=r.get("key"),
                mood=r.get("mood"),
                energy=r.get("energy"),
                instrument=r.get("instrument"),
            )
            sample = SampleRepository.upsert(data)
            imported += 1
            results.append({"id": sample.id, "filename": file, "path": file_path, **r})
            if not json_output:
                print(
                    f"  {file:<36} {str(r.get('bpm', '?')):<7} {r.get('key', '?'):<10} "
                    f"{r.get('energy', '?'):<7} {r.get('mood', '?'):<12} {r.get('instrument', '?')}",
                    file=sys.stderr,
                )
        except Exception as e:  # noqa: BLE001
            errors += 1
            if not json_output:
                print(f"  ❌ {file} — failed: {e}", file=sys.stderr)

    if json_output:
        print(json.dumps({"imported": imported, "errors": errors, "samples": results}))
    else:
        print(f"\n✔ Imported {imported} / {len(wav_files)} samples.", file=sys.stderr)
