"""
Synthetic Audio Sample Generator for Testing

Generates diverse, realistic audio samples programmatically:
- Kicks, snares, hi-hats, bass, pads, leads
- Variable BPM, pitch, duration, energy
- Deterministic (same seed = same output)
- Fast generation (<10ms per sample)
"""

from __future__ import annotations

import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Literal

# Type aliases
Instrument = Literal["kick", "snare", "hihat", "bass", "pad", "lead", "loop"]
Energy = Literal["low", "mid", "high"]


class SampleGenerator:
    """Generate synthetic audio samples for testing"""
    
    def __init__(self, sr: int = 44100, seed: int = 42):
        self.sr = sr
        self.rng = np.random.default_rng(seed)
    
    def generate_kick(
        self,
        bpm: int = 140,
        duration: float = 0.5,
        pitch: int = 60,
        energy: Energy = "mid"
    ) -> np.ndarray:
        """Generate synthetic kick drum with pitch and energy control"""
        samples = int(self.sr * duration)
        t = np.linspace(0, duration, samples)
        
        # Base frequency from MIDI pitch
        freq = 55 * (2 ** ((pitch - 60) / 12))
        
        # Energy affects decay rate
        decay_rate = {"low": 5, "mid": 10, "high": 15}[energy]
        
        # Sine wave with exponential decay
        audio = np.sin(2 * np.pi * freq * t) * np.exp(-decay_rate * t)
        
        # Add click transient for realism
        click = self.rng.normal(0, 0.3, samples) * np.exp(-100 * t)
        audio = audio + click
        
        return self._normalize(audio)
    
    def generate_snare(
        self,
        duration: float = 0.3,
        energy: Energy = "mid"
    ) -> np.ndarray:
        """Generate synthetic snare drum"""
        samples = int(self.sr * duration)
        t = np.linspace(0, duration, samples)
        
        # Tone component (200 Hz)
        tone = np.sin(2 * np.pi * 200 * t) * np.exp(-15 * t)
        
        # Noise component (snare rattle)
        noise = self.rng.normal(0, 0.5, samples) * np.exp(-10 * t)
        
        # Energy affects mix
        tone_mix = {"low": 0.3, "mid": 0.5, "high": 0.7}[energy]
        audio = tone_mix * tone + (1 - tone_mix) * noise
        
        return self._normalize(audio)
    
    def generate_hihat(
        self,
        duration: float = 0.1,
        energy: Energy = "mid",
        closed: bool = True
    ) -> np.ndarray:
        """Generate synthetic hi-hat (closed or open)"""
        samples = int(self.sr * duration)
        t = np.linspace(0, duration, samples)
        
        # High-frequency noise
        noise = self.rng.normal(0, 1, samples)
        
        # High-pass filter (simulate metallic sound)
        from scipy.signal import butter, filtfilt
        b, a = butter(4, 8000 / (self.sr / 2), btype='high')
        noise = filtfilt(b, a, noise)
        
        # Envelope
        if closed:
            envelope = np.exp(-50 * t)
        else:
            envelope = np.exp(-10 * t)  # Slower decay for open
        
        # Energy affects amplitude
        amp = {"low": 0.3, "mid": 0.6, "high": 1.0}[energy]
        audio = amp * noise * envelope
        
        return self._normalize(audio)
    
    def generate_bass_loop(
        self,
        bpm: int = 140,
        bars: int = 1,
        key: str = "Am"
    ) -> np.ndarray:
        """Generate synthetic bass loop"""
        # Calculate duration from BPM
        beat_duration = 60 / bpm
        duration = beat_duration * 4 * bars  # 4 beats per bar
        samples = int(self.sr * duration)
        
        # Parse key (e.g., "Am" -> A, minor)
        note_name = key[0]
        is_minor = "m" in key.lower()
        
        # MIDI note number
        note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        base_note = 36 + note_map[note_name]  # Start at C2
        
        # Generate simple bassline pattern
        pattern = [0, 0, 7, 0] if is_minor else [0, 0, 4, 0]  # Root, root, fifth/third, root
        audio = np.zeros(samples)
        
        for i, interval in enumerate(pattern):
            note = base_note + interval
            freq = 440 * (2 ** ((note - 69) / 12))
            
            # Note timing
            start = int(i * beat_duration * self.sr)
            end = int((i + 0.9) * beat_duration * self.sr)  # 90% duty cycle
            note_samples = end - start
            
            # Generate note
            t = np.linspace(0, note_samples / self.sr, note_samples)
            note_audio = np.sin(2 * np.pi * freq * t)
            
            # Envelope
            attack = int(0.01 * self.sr)
            release = int(0.1 * self.sr)
            envelope = np.ones(note_samples)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            
            audio[start:end] = note_audio * envelope
        
        return self._normalize(audio)
    
    def generate_pad(
        self,
        duration: float = 2.0,
        key: str = "Am",
        energy: Energy = "low"
    ) -> np.ndarray:
        """Generate synthetic pad/chord"""
        samples = int(self.sr * duration)
        t = np.linspace(0, duration, samples)
        
        # Parse key
        note_name = key[0]
        is_minor = "m" in key.lower()
        note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        base_note = 60 + note_map[note_name]  # Start at C4
        
        # Chord intervals
        if is_minor:
            intervals = [0, 3, 7]  # Minor triad
        else:
            intervals = [0, 4, 7]  # Major triad
        
        # Generate chord
        audio = np.zeros(samples)
        for interval in intervals:
            note = base_note + interval
            freq = 440 * (2 ** ((note - 69) / 12))
            audio += np.sin(2 * np.pi * freq * t)
        
        # Smooth envelope
        attack = int(0.1 * self.sr)
        release = int(0.2 * self.sr)
        envelope = np.ones(samples)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-release:] = np.linspace(1, 0, release)
        
        audio = audio * envelope
        
        # Energy affects amplitude
        amp = {"low": 0.3, "mid": 0.5, "high": 0.7}[energy]
        audio = amp * audio
        
        return self._normalize(audio)
    
    def generate_lead(
        self,
        duration: float = 1.0,
        bpm: int = 140,
        key: str = "Am",
        energy: Energy = "high"
    ) -> np.ndarray:
        """Generate synthetic lead melody"""
        samples = int(self.sr * duration)
        
        # Parse key
        note_name = key[0]
        is_minor = "m" in key.lower()
        note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        base_note = 72 + note_map[note_name]  # Start at C5
        
        # Simple melody pattern
        if is_minor:
            pattern = [0, 3, 7, 10, 7, 3]  # Minor scale run
        else:
            pattern = [0, 4, 7, 11, 7, 4]  # Major scale run
        
        audio = np.zeros(samples)
        beat_duration = 60 / bpm
        note_duration = beat_duration / 2  # 8th notes
        
        for i, interval in enumerate(pattern):
            note = base_note + interval
            freq = 440 * (2 ** ((note - 69) / 12))
            
            start = int(i * note_duration * self.sr)
            end = int((i + 0.9) * note_duration * self.sr)
            if end > samples:
                break
            
            note_samples = end - start
            t = np.linspace(0, note_samples / self.sr, note_samples)
            
            # Sawtooth wave for lead sound
            note_audio = 2 * (t * freq - np.floor(t * freq + 0.5))
            
            # Envelope
            attack = int(0.005 * self.sr)
            release = int(0.05 * self.sr)
            envelope = np.ones(note_samples)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            
            audio[start:end] = note_audio * envelope
        
        # Energy affects amplitude
        amp = {"low": 0.4, "mid": 0.6, "high": 0.8}[energy]
        audio = amp * audio
        
        return self._normalize(audio)
    
    def _normalize(self, audio: np.ndarray, target: float = 0.8) -> np.ndarray:
        """Normalize audio to target peak amplitude"""
        peak = np.abs(audio).max()
        if peak > 0:
            audio = audio * (target / peak)
        return audio
    
    def save(self, audio: np.ndarray, path: Path | str):
        """Save audio to WAV file"""
        sf.write(str(path), audio, self.sr)


def generate_test_library(output_dir: Path, count: int = 100) -> dict:
    """
    Generate a complete test library with diverse samples
    
    Returns:
        dict with counts by instrument type
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    gen = SampleGenerator()
    counts = {}
    
    # Generate kicks (25 samples)
    for bpm in [120, 130, 140, 150, 160]:
        for energy in ["low", "mid", "high"]:
            for i in range(2):
                audio = gen.generate_kick(bpm=bpm, energy=energy)
                filename = f"kick_{bpm}bpm_{energy}_{i}.wav"
                gen.save(audio, output_dir / filename)
                counts["kick"] = counts.get("kick", 0) + 1
    
    # Generate snares (15 samples)
    for energy in ["low", "mid", "high"]:
        for i in range(5):
            audio = gen.generate_snare(energy=energy)
            filename = f"snare_{energy}_{i}.wav"
            gen.save(audio, output_dir / filename)
            counts["snare"] = counts.get("snare", 0) + 1
    
    # Generate hi-hats (20 samples)
    for closed in [True, False]:
        for energy in ["low", "mid", "high"]:
            for i in range(3):
                audio = gen.generate_hihat(energy=energy, closed=closed)
                hat_type = "closed" if closed else "open"
                filename = f"hihat_{hat_type}_{energy}_{i}.wav"
                gen.save(audio, output_dir / filename)
                counts["hihat"] = counts.get("hihat", 0) + 1
    
    # Generate bass loops (20 samples)
    for bpm in [120, 140, 160, 180]:
        for key in ["Am", "Dm", "Em", "Gm", "C"]:
            audio = gen.generate_bass_loop(bpm=bpm, key=key)
            filename = f"bass_{bpm}bpm_{key}.wav"
            gen.save(audio, output_dir / filename)
            counts["bass"] = counts.get("bass", 0) + 1
    
    # Generate pads (10 samples)
    for key in ["Am", "Dm", "C", "G", "Em"]:
        for energy in ["low", "mid"]:
            audio = gen.generate_pad(key=key, energy=energy)
            filename = f"pad_{key}_{energy}.wav"
            gen.save(audio, output_dir / filename)
            counts["pad"] = counts.get("pad", 0) + 1
    
    # Generate leads (10 samples)
    for bpm in [140, 150]:
        for key in ["Am", "Dm", "C", "G", "Em"]:
            audio = gen.generate_lead(bpm=bpm, key=key)
            filename = f"lead_{bpm}bpm_{key}.wav"
            gen.save(audio, output_dir / filename)
            counts["lead"] = counts.get("lead", 0) + 1
    
    return counts


if __name__ == "__main__":
    # Generate test library
    output = Path("tests/fixtures/generated")
    counts = generate_test_library(output, count=100)
    
    print(f"✅ Generated {sum(counts.values())} samples:")
    for instrument, count in sorted(counts.items()):
        print(f"  - {instrument}: {count}")
