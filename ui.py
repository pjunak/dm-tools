import sys
import os
import pygame
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QDockWidget, QTreeWidgetItem, QTreeWidget
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QTimer
from music_player import MusicPlayer
from folder_tree import FolderTree

# Suppress PyGame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
pygame.mixer.init()

class DMToolsUI(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.music_player = MusicPlayer(debug=self.debug)
        self.is_playing = False  # Track if music is currently playing or paused
        self.is_paused = False   # Track if music is paused
        self.root_dir = None     # To store the current folder
        self.repeat_mode = "none"  # Repeat mode (none, one, all)

        # Set the window icon using the provided icon
        self.setWindowIcon(QIcon("media/iconA.png"))  # Using iconA (transparent)

        self.init_ui()

    def init_ui(self):
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

        # Initialize the toggle button on the right edge
        self.init_playlist_toggle_button()

        # Set up timer to constantly check for window resizing and keep button on the right edge
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_toggle_button_position)
        self.timer.start(100)  # Update every 100ms

    def create_menu(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')
        open_action = file_menu.addAction(QIcon("media/idon.png"), 'Open Folder')  # Using idon.png
        open_action.triggered.connect(self.open_folder)
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        # Settings Menu
        settings_menu = menubar.addMenu('Settings')

        # Checkable Shuffle Action
        self.shuffle_action = QAction(QIcon("media/icon_big.png"), 'Shuffle', self)  # Using icon_big.png
        self.shuffle_action.setCheckable(True)
        self.shuffle_action.toggled.connect(self.toggle_shuffle)
        settings_menu.addAction(self.shuffle_action)

        # Repeat Button to switch modes
        self.repeat_action = QAction(f"Repeat: {self.repeat_mode.capitalize()}", self)
        self.repeat_action.triggered.connect(self.switch_repeat_mode)
        settings_menu.addAction(self.repeat_action)

    def init_controls(self):
        """Initialize the control buttons (Play, Pause, Stop, Shuffle, Repeat) at the bottom."""
        self.control_frame = QWidget(self)
        control_layout = QHBoxLayout()

        # Play/Pause Button
        self.play_pause_button = QPushButton("Play", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        # Stop Button
        stop_button = QPushButton("Stop", self)
        stop_button.clicked.connect(self.stop_music)

        # Add buttons to layout
        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(stop_button)

        self.control_frame.setLayout(control_layout)

    def init_dockable_right_pane(self):
        """Initializes the retractable right pane using QDockWidget."""
        self.dock_widget = QDockWidget("Playlist", self)
        self.dock_widget.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        # Right pane - Playlist
        right_pane = QWidget()
        right_layout = QVBoxLayout()

        # Playlist (QListWidget)
        self.playlist_box = QListWidget()
        self.playlist_box.itemDoubleClicked.connect(self.on_song_double_click)
        right_layout.addWidget(self.playlist_box)

        right_pane.setLayout(right_layout)

        # Set the right pane inside the dockable widget
        self.dock_widget.setWidget(right_pane)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_widget)

    def init_playlist_toggle_button(self):
        """Initialize the toggle button on the right edge for the playlist."""
        self.toggle_playlist_button = QPushButton(">>>", self)
        self.toggle_playlist_button.setFixedWidth(30)  # Set a fixed width for the button
        self.toggle_playlist_button.clicked.connect(self.toggle_playlist)

        # Initial position
        self.update_toggle_button_position()

    def update_toggle_button_position(self):
        """Ensure the toggle button stays on the right edge of the main window."""
        button_height = self.toggle_playlist_button.height()
        self.toggle_playlist_button.move(self.width() - 30, (self.height() // 2) - (button_height // 2))  # Center vertically

    def open_folder(self):
        """Open a folder, stop the current song, and load its contents into the folder tree."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.root_dir = folder
            self.stop_music()
            self.music_player.clear_playlist()
            self.load_folder_tree(self.root_dir)

    def load_folder_tree(self, folder_path):
        """Reload the folder tree structure based on the new root folder."""
        self.folder_tree = FolderTree(folder_path)

        # Check if FolderTree has the 'tree' attribute and handle missing structure
        if not hasattr(self.folder_tree, 'tree') or not isinstance(self.folder_tree.tree, dict):
            print("Error: FolderTree structure is invalid. Please check the FolderTree class implementation.")
            return

        self.tree_view.clear()  # Clear existing tree items
        for subtree in self.folder_tree.tree.get('folders', []):  # Ensure 'folders' key exists
            self.populate_tree(self.tree_view, subtree)


    def populate_tree(self, tree_view, tree_data, parent=None):
        """Populate the folder tree with subdirectories."""
        node = QTreeWidgetItem([os.path.basename(tree_data['path'])])
        node.setData(0, Qt.ItemDataRole.UserRole, tree_data['path'])  # Store the folder path

        if parent is None:
            # Add to the top level if no parent is provided
            tree_view.addTopLevelItem(node)
        else:
            # Otherwise, add as a child of the parent node
            parent.addChild(node)

        # Recursively add subfolders to the tree view
        for subtree in tree_data['folders']:
            self.populate_tree(tree_view, subtree, node)



    def on_folder_double_click(self, item):
        """Load playlist from the selected folder in the folder tree."""
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        if os.path.isdir(folder_path):
            self.stop_music()
            self.music_player.clear_playlist()
            self.music_player.load_playlist(folder_path)
            self.update_playlist_display()

    def on_song_double_click(self, item):
        """Play the selected song when double-clicked in the playlist."""
        song_idx = self.playlist_box.row(item)
        self.stop_music()
        self.music_player.play_from_index(song_idx)
        self.is_playing = True
        self.is_paused = False
        self.play_pause_button.setText("Pause")
        self.update_playlist_display()

    def update_playlist_display(self):
        """Update the playlist view with the current playlist and highlight the current song."""
        self.playlist_box.clear()
        for song in self.music_player.playlist:
            self.playlist_box.addItem(os.path.basename(song))

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

    def start_playback(self):
        """Start playing the selected song, or the first song if none selected."""
        selected_item = self.playlist_box.currentItem()
        if not selected_item:
            self.playlist_box.setCurrentRow(0)
            selected_item = self.playlist_box.item(0)
        song_idx = self.playlist_box.row(selected_item)
        self.music_player.play_from_index(song_idx)
        self.is_playing = True
        self.is_paused = False
        self.play_pause_button.setText("Pause")
        self.update_playlist_display()

    def stop_music(self):
        """Stop the music and reset the playlist state."""
        self.music_player.stop_music()
        self.is_playing = False
        self.is_paused = False
        self.play_pause_button.setText("Play")
        self.update_playlist_display()

    def toggle_shuffle(self, state):
        """Toggle shuffle mode on/off."""
        if self.shuffle_action.isChecked():
            self.music_player.shuffle_playlist()
        self.update_playlist_display()

    def switch_repeat_mode(self):
        """Switch between repeat modes (none, one, all)."""
        if self.repeat_mode == "none":
            self.repeat_mode = "all"
        elif self.repeat_mode == "all":
            self.repeat_mode = "one"
        else:
            self.repeat_mode = "none"
        self.repeat_action.setText(f"Repeat: {self.repeat_mode.capitalize()}")

    def toggle_playlist(self):
        """Toggle the visibility of the playlist dock and adjust button."""
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
            self.toggle_playlist_button.setText(">>>")  # Pointing out when closed
        else:
            self.dock_widget.show()
            self.toggle_playlist_button.setText("<<<")  # Pointing inward when open


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DMToolsUI(debug=True)
    window.show()
    sys.exit(app.exec())
