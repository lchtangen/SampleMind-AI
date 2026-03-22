import os
from analyzer.audio_analysis import analyze_file

def analyze_samples(folder: str):
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return

    wav_files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]
    if not wav_files:
        print("⚠️ No WAV files found.")
        return

    for file in wav_files:
        file_path = os.path.join(folder, file)
        try:
            bpm, key = analyze_file(file_path)
            print(f"✅ {file} — BPM: {bpm}, Key: {key}")
        except Exception as e:
            print(f"❌ Failed to analyze {file}: {e}")
