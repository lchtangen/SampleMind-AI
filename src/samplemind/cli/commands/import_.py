"""Import WAV samples into the library."""

import os
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.data.database import init_db, save_sample


def import_samples(source: str):
    """Import all WAV files from a folder and analyze + store them."""
    if not os.path.exists(source):
        print(f"❌ Folder not found: {source}")
        return

    wav_files = [f for f in os.listdir(source) if f.lower().endswith(".wav")]
    if not wav_files:
        print("⚠️ No WAV files found in folder.")
        return

    init_db()
    print(f"📂 Found {len(wav_files)} WAV file(s) in: {source}\n")
    print(f"  {'Filename':<36} {'BPM':<7} {'Key':<10} {'Energy':<7} {'Mood':<12} {'Type'}")
    print("  " + "─" * 78)

    imported = 0
    for file in wav_files:
        file_path = os.path.abspath(os.path.join(source, file))
        try:
            r = analyze_file(file_path)
            save_sample(
                filename=file, path=file_path,
                bpm=r["bpm"], key=r["key"],
                mood=r["mood"], energy=r["energy"],
                instrument=r["instrument"],
            )
            imported += 1
            print(f"  {file:<36} {str(r['bpm']):<7} {r['key']:<10} "
                  f"{r['energy']:<7} {r['mood']:<12} {r['instrument']}")
        except Exception as e:
            print(f"  ❌ {file} — failed: {e}")

    print(f"\n✔ Imported {imported} / {len(wav_files)} samples.")
