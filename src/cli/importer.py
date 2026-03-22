import os
from analyzer.audio_analysis import analyze_file
from data.database import init_db, save_sample


def import_samples(source: str):
    if not os.path.exists(source):
        print(f"❌ Folder not found: {source}")
        return

    wav_files = [f for f in os.listdir(source) if f.lower().endswith(".wav")]
    if not wav_files:
        print("⚠️ No WAV files found in folder.")
        return

    init_db()  # create the DB table if this is the first run
    print(f"📂 Found {len(wav_files)} WAV file(s) in: {source}\n")

    imported = 0
    for file in wav_files:
        file_path = os.path.abspath(os.path.join(source, file))
        try:
            bpm, key = analyze_file(file_path)
            save_sample(filename=file, path=file_path, bpm=bpm, key=key)
            imported += 1
            print(f"  ✅ {file:40s} BPM: {bpm:<6} Key: {key}")
        except Exception as e:
            print(f"  ❌ {file} — failed: {e}")

    print(f"\n✔ Imported {imported} / {len(wav_files)} samples into library.")
