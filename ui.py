import logging
import sys
import os
import pygame
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QDockWidget, QTreeWidgetItem, QTreeWidget, QProgressBar
from PyQt6.QtGui import QAction, QIcon, QColor
from PyQt6.QtCore import Qt, QTimer
from music_player import MusicPlayer
from folder_tree import FolderTree
from spectrogram import generate_spectrogram_data
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QThread, pyqtSignal

# Suppress PyGame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
pygame.mixer.init()

# Logger configuration
def setup_logger(debug: bool) -> logging.Logger:
    logger = logging.getLogger('DMTools')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Log to file
    file_handler = logging.FileHandler('dm_tools_debug.log')
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Log to console (optional, comment out if not needed)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class SpectrogramThread(QThread):
    finished = pyqtSignal(object, object, float)

    def __init__(self, audio_file: str, logger: logging.Logger) -> None:
        super().__init__()
        self.audio_file = audio_file
        self.logger = logger

    def run(self) -> None:
        """Run the spectrogram data generation in a separate thread."""
        self.logger.debug(f"Generating spectrogram for: {self.audio_file}")
        waveform, energy, tempo = generate_spectrogram_data(self.audio_file, include_bpm=False)
        self.logger.debug(f"Finished generating spectrogram for: {self.audio_file}")
        self.finished.emit(waveform, energy, tempo)

class DMToolsUI(QMainWindow):
    def __init__(self, debug=False):
        self.logger = setup_logger(debug)  # Initialize logger
        self.logger.debug("DMToolsUI initialized in debug mode" if debug else "DMToolsUI initialized in normal mode")

        super().__init__()
        self.debug = debug
        self.music_player = MusicPlayer(debug=self.debug)
        self.is_playing = False  # Track if music is currently playing or paused
        self.is_paused = False   # Track if music is paused
        self.root_dir = None     # To store the current folder
        self.repeat_mode = "none"  # Repeat mode (none, one, playlist)
        self.current_song_idx = None  # Store the current playing song index

        # Set the window icon using both icons
        self.setWindowIcon(QIcon("media/iconA.png"))  # Primary icon for the app
        self.setWindowIcon(QIcon("media/icon.png"))  # Alternate icon if desired

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the UI elements."""
        self.logger.debug("Initializing UI...")
        self.setWindowTitle("Dungeon Master Music Player")
        self.setGeometry(100, 100, 800, 600)

        # Menu Bar
        self.create_menu()

        # Splitter between tree and dockable playlist/control panel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pane - Treeview for folder navigation
        self.tree_view = QTreeWidget()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.itemDoubleClicked.connect(self.on_folder_double_click)
        splitter.addWidget(self.tree_view)

        # Right pane - Playlist and control buttons inside a dockable window
        self.init_dockable_right_pane()

        # Add controls to the bottom of the main window (not docked)
        self.init_controls()

        # Add the splitter to the central widget
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.control_frame)  # Add controls below the splitter

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initialize the spectrogram and progress bar window first
        self.init_spectrogram_window()

        # Initialize the toggle buttons
        self.init_toggle_buttons()

        # Hide the playlist and spectrogram subwindows by default
        self.dock_widget.hide()
        self.spectrogram_dock.hide()

        # Connect the dock widget's visibilityChanged signals to control the toggle button visibility
        self.dock_widget.visibilityChanged.connect(self.handle_playlist_visibility)
        self.spectrogram_dock.visibilityChanged.connect(self.handle_spectrogram_visibility)

        # Set up timer to constantly check for window resizing and keep buttons positioned correctly
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_toggle_button_positions)
        self.timer.start(100)  # Update every 100ms

    def create_menu(self) -> None:
        self.logger.debug("Creating menu...")
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')
        open_action = file_menu.addAction(QIcon("media/idon.png"), 'Open Folder')  # Using idon.png
        open_action.triggered.connect(self.open_folder)
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        # Settings Menu (For future use)
        settings_menu = menubar.addMenu('Settings')

    def init_controls(self) -> None:
        """Initialize the control buttons (Play, Pause, Stop) at the bottom."""
        self.logger.debug("Initializing control buttons...")
        self.control_frame = QWidget(self)
        control_layout = QHBoxLayout()

        # Play/Pause Button
        self.play_pause_button = QPushButton("Play", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        # Stop Button
        stop_button = QPushButton("Stop", self)
        stop_button.clicked.connect(self.stop_music)

        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(stop_button)

        self.control_frame.setLayout(control_layout)

    def init_dockable_right_pane(self) -> None:
        """Initializes the retractable right pane using QDockWidget."""
        self.logger.debug("Initializing retractable right pane...")
        self.dock_widget = QDockWidget("Playlist", self)
        self.dock_widget.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        right_pane = QWidget()
        right_layout = QVBoxLayout()

        # Shuffle Button (action button, not toggle)
        self.shuffle_button = QPushButton("Shuffle", self)
        self.shuffle_button.clicked.connect(self.shuffle_playlist)
        right_layout.addWidget(self.shuffle_button)

        # Repeat Button (cycle through None, One, Playlist)
        self.repeat_button = QPushButton(f"Repeat: {self.repeat_mode.capitalize()}", self)
        self.repeat_button.clicked.connect(self.cycle_repeat_mode)
        right_layout.addWidget(self.repeat_button)

        # Playlist (QListWidget)
        self.playlist_box = QListWidget()
        self.playlist_box.itemDoubleClicked.connect(self.on_song_double_click)
        right_layout.addWidget(self.playlist_box)

        right_pane.setLayout(right_layout)

        self.dock_widget.setWidget(right_pane)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_widget)
        
    def start_playback(self):
        """Start playing the selected song."""
        selected_item = self.playlist_box.currentItem()
        if not selected_item:
            self.playlist_box.setCurrentRow(0)
            selected_item = self.playlist_box.item(0)
        song_idx = self.playlist_box.row(selected_item)
        
        # Stop any currently playing music
        self.stop_music()
        
        # Play the selected song from the playlist
        self.music_player.play_from_index(song_idx)
        self.is_playing = True
        self.is_paused = False
        self.current_song_idx = song_idx
        self.play_pause_button.setText("Pause")
        
        # Update the playlist display to highlight the playing song
        self.update_playlist_display()
        
        # Generate and display the spectrogram
        if self.spectrogram_dock.isVisible():
            self.show_spectrogram()

        
    def update_playlist_display(self) -> None:
        """Update the playlist view with the current playlist and highlight the current song."""
        self.logger.debug("Updating playlist display...")
        self.playlist_box.clear()

        for idx, song in enumerate(self.music_player.playlist):
            item = os.path.basename(song)
            self.playlist_box.addItem(item)

            # Highlight the currently playing song
            if idx == self.current_song_idx:
                self.playlist_box.item(idx).setBackground(QColor(80, 80, 80))  # Use dark grey
                font = self.playlist_box.item(idx).font()
                font.setBold(True)
                self.playlist_box.item(idx).setFont(font)

        
    def init_spectrogram_window(self) -> None:
        """Initialize the spectrogram display area and progress bar."""
        self.logger.debug("Initializing spectrogram window...")
        
        # Create the dockable widget for the spectrogram
        self.spectrogram_dock = QDockWidget("Spectrogram", self)
        self.spectrogram_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        # Create a widget for holding the spectrogram and progress bar
        spectrogram_widget = QWidget()
        spectrogram_layout = QVBoxLayout()

        # Progress bar for song position
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        spectrogram_layout.addWidget(self.progress_bar)

        # Spectrogram display area using matplotlib canvas
        self.spectrogram_canvas = FigureCanvas(Figure(figsize=(10, 3)))
        spectrogram_layout.addWidget(self.spectrogram_canvas)

        spectrogram_widget.setLayout(spectrogram_layout)

        self.spectrogram_dock.setWidget(spectrogram_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.spectrogram_dock)


    def open_folder(self) -> None:
        """Open a folder, stop the current song, and load its contents into the folder tree."""
        self.logger.debug("Opening folder dialog...")
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.logger.debug(f"Folder selected: {folder}")
            self.root_dir = folder
            self.stop_music()
            self.music_player.clear_playlist()
            self.load_folder_tree(self.root_dir)
        else:
            self.logger.debug("No folder selected.")

    def load_folder_tree(self, folder_path: str) -> None:
        """Reload the folder tree structure based on the new root folder."""
        try:
            self.logger.debug(f"Loading folder tree for path: {folder_path}")
            folder_path = folder_path.encode('utf-8').decode('utf-8')  # Handle non-ASCII characters
            self.folder_tree = FolderTree(folder_path)

            if not hasattr(self.folder_tree, 'tree') or not isinstance(self.folder_tree.tree, dict):
                self.logger.error("Error: FolderTree structure is invalid.")
                return

            self.tree_view.clear()
            for subtree in self.folder_tree.tree.get('folders', []):
                self.populate_tree(self.tree_view, subtree)
        except Exception as e:
            self.logger.error(f"Failed to load folder tree: {e}")


    def populate_tree(self, tree_view: QTreeWidget, tree_data: dict, parent: QTreeWidgetItem = None) -> None:
        """Populate the folder tree with subdirectories."""
        self.logger.debug(f"Populating tree with: {tree_data['path']}")
        node = QTreeWidgetItem([os.path.basename(tree_data['path'])])
        node.setData(0, Qt.ItemDataRole.UserRole, tree_data['path'])

        if parent is None:
            tree_view.addTopLevelItem(node)
        else:
            parent.addChild(node)

        for subtree in tree_data['folders']:
            self.populate_tree(tree_view, subtree, node)

    def on_folder_double_click(self, item: QTreeWidgetItem) -> None:
        """Load playlist from the selected folder in the folder tree but keep the current song playing."""
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        self.logger.debug(f"Folder double-clicked: {folder_path}")
        if os.path.isdir(folder_path):
            self.music_player.clear_playlist()
            self.music_player.load_playlist(folder_path)
            self.update_playlist_display()

    def on_song_double_click(self, item: QListWidget) -> None:
        """Play the selected song when double-clicked in the playlist."""
        song_idx = self.playlist_box.row(item)
        self.logger.debug(f"Song double-clicked: {song_idx}")
        self.stop_music()
        self.music_player.play_from_index(song_idx)
        self.is_playing = True
        self.is_paused = False
        self.current_song_idx = song_idx
        self.play_pause_button.setText("Pause")
        self.update_playlist_display()

        # Clear current spectrogram and generate the new one
        self.clear_spectrogram()
        if self.spectrogram_dock.isVisible():
            self.show_spectrogram()

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if self.is_playing and not self.is_paused:
            self.music_player.pause_music()
            self.is_paused = True
            self.play_pause_button.setText("Play")
        elif self.is_paused:
            self.music_player.resume_music()
            self.is_paused = False
            self.play_pause_button.setText("Pause")
        else:
            self.start_playback()

    def stop_music(self) -> None:
        """Stop the music and reset the playlist state."""
        self.logger.debug("Stopping music")
        self.music_player.stop_music()
        self.is_playing = False
        self.is_paused = False
        self.current_song_idx = None
        self.play_pause_button.setText("Play")
        self.update_playlist_display()

    def shuffle_playlist(self) -> None:
        """Shuffle the playlist and refresh the display."""
        self.logger.debug("Shuffling playlist")
        self.music_player.shuffle_playlist()
        self.update_playlist_display()

    def cycle_repeat_mode(self) -> None:
        """Cycle between repeat modes: None, One, Playlist."""
        self.logger.debug("Cycling repeat mode")
        if self.repeat_mode == "none":
            self.repeat_mode = "playlist"
        elif self.repeat_mode == "playlist":
            self.repeat_mode = "one"
        else:
            self.repeat_mode = "none"
        self.repeat_button.setText(f"Repeat: {self.repeat_mode.capitalize()}")

    def show_spectrogram(self) -> None:
        """Generate and display the spectrogram in a docked widget, only if the subwindow is visible."""
        if not self.spectrogram_dock.isVisible():
            self.logger.debug("Spectrogram window is closed. Not generating spectrogram.")
            return

        if self.current_song_idx is not None:
            audio_file = self.music_player.playlist[self.current_song_idx]
            self.logger.debug(f"Generating spectrogram for song at index {self.current_song_idx}")

            # Terminate existing spectrogram thread if running
            if hasattr(self, 'spectrogram_thread') and self.spectrogram_thread.isRunning():
                self.spectrogram_thread.terminate()

            # Create a new background thread for spectrogram data generation
            self.spectrogram_thread = SpectrogramThread(audio_file, self.logger)
            self.spectrogram_thread.finished.connect(self.plot_spectrogram)
            self.spectrogram_thread.start()

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

    def clear_spectrogram(self) -> None:
        """Clear the current spectrogram."""
        self.logger.debug("Clearing spectrogram")
        self.spectrogram_canvas.figure.clear()
        self.spectrogram_canvas.draw()

    def handle_playlist_visibility(self, visible: bool) -> None:
        """Handle the visibility of the playlist dock widget."""
        self.logger.debug(f"Playlist visibility changed: {'Visible' if visible else 'Hidden'}")
        if visible:
            self.toggle_playlist_button.hide()
        else:
            self.toggle_playlist_button.setText(">>>")
            self.toggle_playlist_button.show()

    def handle_spectrogram_visibility(self, visible: bool) -> None:
        """Handle the visibility of the spectrogram subwindow."""
        self.logger.debug(f"Spectrogram visibility changed: {'Visible' if visible else 'Hidden'}")
        if visible:
            self.toggle_spectrogram_button.hide()
            self.show_spectrogram()
        else:
            self.toggle_spectrogram_button.show()
            self.clear_spectrogram()


    def init_toggle_buttons(self) -> None:
        """Initialize the toggle buttons for playlist and spectrogram subwindows."""
        self.logger.debug("Initializing toggle buttons for playlist and spectrogram...")

        # Playlist toggle button
        self.toggle_playlist_button = QPushButton(">>>", self)
        self.toggle_playlist_button.setFixedWidth(30)
        self.toggle_playlist_button.clicked.connect(self.toggle_playlist)

        # Spectrogram toggle button
        self.toggle_spectrogram_button = QPushButton(">>>", self)
        self.toggle_spectrogram_button.setFixedWidth(30)
        self.toggle_spectrogram_button.clicked.connect(self.toggle_spectrogram)

        # Initial positions
        self.update_toggle_button_positions()


    def update_toggle_button_positions(self) -> None:
        """Ensure the toggle buttons stay positioned at the correct edges."""
        playlist_button_height = self.toggle_playlist_button.height()
        spectrogram_button_height = self.toggle_spectrogram_button.height()

        # Position the playlist button at the top right edge
        self.toggle_playlist_button.move(self.width() - 50, 30)

        # Position the spectrogram button at the bottom right edge
        self.toggle_spectrogram_button.move(self.width() - 50, self.height() - spectrogram_button_height - 30)


    def toggle_playlist(self) -> None:
        """Toggle the visibility of the playlist dock."""
        self.logger.debug(f"Toggling playlist visibility. Currently {'Visible' if self.dock_widget.isVisible() else 'Hidden'}")
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def toggle_spectrogram(self) -> None:
        """Toggle the visibility of the spectrogram dock."""
        self.logger.debug(f"Toggling spectrogram visibility. Currently {'Visible' if self.spectrogram_dock.isVisible() else 'Hidden'}")
        if self.spectrogram_dock.isVisible():
            self.spectrogram_dock.hide()
        else:
            self.spectrogram_dock.show()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = DMToolsUI(debug=True)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.exception("Application crashed with an error.")
        sys.exit(1)
