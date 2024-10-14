import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import find_peaks
import logging

def generate_spectrogram_data(audio_file: str, include_bpm: bool = True) -> tuple:
    logger = logging.getLogger('DMTools.Spectrogram')
    logger.debug(f"Loading audio file: {audio_file}")

    try:
        sample_rate, samples = wavfile.read(audio_file)
    except ValueError as e:
        logger.error(f"Error reading file {audio_file}: {e}")
        return np.array([]), np.array([]), 0

    logger.debug(f"Audio loading completed. Sample rate: {sample_rate}, Samples: {len(samples)}")

    # Compute waveform and energy
    waveform = samples / np.max(np.abs(samples))  # Normalize waveform
    energy = np.abs(waveform)

    logger.debug("Energy calculation completed.")

    # Calculate BPM using peak finding (optional)
    bpm = 0
    if include_bpm:
        peaks, _ = find_peaks(energy, height=0.05, distance=sample_rate * 0.5)
        bpm = (len(peaks) / (len(samples) / sample_rate)) * 60
        logger.debug(f"BPM calculation completed. Estimated BPM: {bpm}")

    return waveform, energy, bpm

def plot_spectrogram(self, waveform: np.ndarray, energy: np.ndarray, tempo: float) -> None:
    """Plot the spectrogram in the main thread using the provided waveform and energy."""
    self.logger.debug("Plotting spectrogram...")

    # Clear the previous plot
    self.spectrogram_canvas.figure.clear()

    # Create a new axes on the canvas
    ax = self.spectrogram_canvas.figure.add_subplot(111)

    # Hide axes (background, ticks, labels)
    ax.set_axis_off()

    # Set background color to match the playlist window (using grey color)
    self.spectrogram_canvas.figure.patch.set_facecolor('#2b2b2b')  # Dark grey color

    # Ensure waveform and energy are scaled correctly over time
    ax.plot(waveform, label="Waveform", color='white', alpha=0.7)

    # Adjust the energy data length to match the waveform
    energy_scaled = np.interp(np.linspace(0, len(waveform), len(energy)), np.arange(len(energy)), energy)
    ax.plot(energy_scaled, label="Energy", color='red', alpha=0.7)

    # Remove margins and padding to make the plot span full width
    ax.margins(0)
    ax.set_position([0, 0, 1, 1])  # Make plot fill the entire figure

    # Draw the updated plot onto the canvas
    self.spectrogram_canvas.draw()
    self.logger.debug("Spectrogram plotted.")

