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

    print(f"\n  {'Filename':<36} {'BPM':<7} {'Key':<10} {'Energy':<7} {'Mood':<12} {'Type'}")
    print("  " + "─" * 78)

    for file in wav_files:
        file_path = os.path.join(folder, file)
        try:
            r = analyze_file(file_path)
            print(f"  {file:<36} {str(r['bpm']):<7} {r['key']:<10} "
                  f"{r['energy']:<7} {r['mood']:<12} {r['instrument']}")
        except Exception as e:
            print(f"  ❌ {file} — failed: {e}")
