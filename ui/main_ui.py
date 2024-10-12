from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from ui.playlist_ui import PlaylistUI
from ui.spectrogram_ui import SpectrogramUI
from logging_utils import setup_logger


class DMToolsUI(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        setup_logger(debug)
        self.setWindowTitle("Dungeon Master Music Player")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()

        # Initialize Playlist and Spectrogram UI components
        self.playlist_ui = PlaylistUI(self)
        self.spectrogram_ui = SpectrogramUI(self)

        # Add components to main layout
        layout.addWidget(self.playlist_ui.playlist_box)
        layout.addWidget(self.spectrogram_ui.spectrogram_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
