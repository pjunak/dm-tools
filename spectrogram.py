import time
import librosa
import numpy as np

def generate_spectrogram_data(audio_file: str, include_bpm: bool = False) -> tuple:
    """Generate waveform, energy, and BPM data for the given audio file."""
    start_time = time.time()

    # Load the audio
    y, sr = librosa.load(audio_file)
    load_time = time.time()
    print(f"Audio loading took {load_time - start_time:.2f} seconds.")

    # Generate waveform (time-domain representation)
    waveform = y

    # Energy (RMS)
    energy = librosa.feature.rms(y=y)[0]
    energy_time = time.time()
    print(f"Energy calculation took {energy_time - load_time:.2f} seconds.")

    # BPM (optional)
    if include_bpm:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    else:
        tempo = 0
    bpm_time = time.time()
    print(f"BPM calculation took {bpm_time - energy_time:.2f} seconds.")

    total_time = bpm_time - start_time
    print(f"Total spectrogram data generation time: {total_time:.2f} seconds.")

    return waveform, energy, tempo
