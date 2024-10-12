from PyQt6.QtWidgets import QListWidget


class PlaylistUI:
    def __init__(self, main_window):
        self.main_window = main_window
        self.playlist_box = QListWidget(main_window)
        self.setup_playlist_ui()

    def setup_playlist_ui(self):
        # Example: You can add setup code for the playlist UI here
        pass
