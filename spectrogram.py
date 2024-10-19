
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import find_peaks
import logging
from logging_utils import setup_logger

# Initialize logger
logger = logging.getLogger('DMTools.Spectrogram')

def generate_spectrogram_data(audio_file: str, include_bpm: bool = True) -> tuple:
    logger.debug(f"Loading audio file: {audio_file}")

    try:
        sample_rate, samples = wavfile.read(audio_file)
    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error reading file {audio_file}: {e}")
        return np.array([]), np.array([]), 0  # Return empty arrays on failure

    # Check if samples are empty or invalid
    if samples is None or len(samples) == 0:
        logger.error(f"No valid data found in file {audio_file}.")
        return np.array([]), np.array([]), 0  # Return empty arrays if samples are empty

    logger.debug(f"Audio loading completed. Sample rate: {sample_rate}, Samples: {len(samples)}")

    # Compute waveform and energy
    waveform = samples / np.max(np.abs(samples))  # Normalize waveform
    energy = np.abs(waveform)

    logger.debug("Energy calculation completed.")

    # Calculate BPM using peak finding (optional)
    bpm = 0
    if include_bpm and len(energy) > 0:
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
    self.spectrogram_canvas.figure.patch.set_facecolor('#2b2b2b')  # Match playlist background

    # Ensure waveform is not empty before plotting
    if len(waveform) == 0:
        self.logger.error("Waveform array is empty. Cannot plot waveform.")
        return  # Stop further execution if waveform is empty
    else:
        # Plot waveform
        ax.plot(waveform, label="Waveform", color='white', alpha=0.7)

    # Ensure energy is not empty before proceeding with interpolation
    if len(energy) == 0:
        self.logger.error("Energy array is empty. Skipping energy plot.")
    else:
        # Adjust the energy data length to match the waveform
        energy_scaled = np.interp(np.linspace(0, len(waveform), len(energy)), np.arange(len(energy)), energy)
        ax.plot(energy_scaled, label="Energy", color='red', alpha=0.7)

    # Remove margins and padding to make the plot span full width
    ax.margins(0)
    ax.set_position([0, 0, 1, 1])  # Make plot fill the entire figure

    # Draw the updated plot onto the canvas
    self.spectrogram_canvas.draw()
    self.logger.debug("Spectrogram plotted.")
