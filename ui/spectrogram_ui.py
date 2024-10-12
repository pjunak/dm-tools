from PyQt6.QtWidgets import QLabel


class SpectrogramUI:
    def __init__(self, main_window):
        self.main_window = main_window
        self.spectrogram_widget = QLabel("Spectrogram goes here")
        self.setup_spectrogram_ui()

    def setup_spectrogram_ui(self):
        # Example: Setup code for spectrogram widget
        pass
