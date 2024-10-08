import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeView, QSplitter, QListWidget, QPushButton, QVBoxLayout, QWidget, QMenuBar, QFileDialog, QDockWidget
from PyQt6.QtCore import Qt
from music_player import MusicPlayer
from folder_tree import FolderTree

class DMToolsUI(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.music_player = MusicPlayer(debug=self.debug)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Dungeon Master Music Player")
        self.setGeometry(100, 100, 800, 600)

        # Menu Bar
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')
        open_action = file_menu.addAction('Open Folder')
        open_action.triggered.connect(self.open_folder)
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        # Playback Menu
        playback_menu = menubar.addMenu('Playback')
        play_action = playback_menu.addAction('Play')
        play_action.triggered.connect(self.toggle_play_pause)
        stop_action = playback_menu.addAction('Stop')
        stop_action.triggered.connect(self.stop_music)

        # Settings Menu
        settings_menu = menubar.addMenu('Settings')
        shuffle_action = settings_menu.addAction('Shuffle')
        shuffle_action.triggered.connect(self.toggle_shuffle)
        repeat_action = settings_menu.addAction('Repeat All')
        repeat_action.triggered.connect(self.toggle_repeat)

        # Splitter between tree and dockable playlist/control panel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pane - Treeview
        self.tree_view = QTreeView()
        splitter.addWidget(self.tree_view)

        # Right pane (will be dockable)
        self.init_dockable_right_pane()

        self.setCentralWidget(splitter)

    def init_dockable_right_pane(self):
        """Initializes the retractable right pane using QDockWidget."""
        dock_widget = QDockWidget("Playlist and Controls", self)
        dock_widget.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        # Right pane - Playlist and control buttons
        right_pane = QWidget()
        right_layout = QVBoxLayout()

        # Playlist (QListWidget)
        self.playlist_box = QListWidget()
        right_layout.addWidget(self.playlist_box)

        # Control buttons
        play_button = QPushButton("Play")
        stop_button = QPushButton("Stop")
        right_layout.addWidget(play_button)
        right_layout.addWidget(stop_button)

        # Connecting buttons to player functionality
        play_button.clicked.connect(self.toggle_play_pause)
        stop_button.clicked.connect(self.stop_music)

        right_pane.setLayout(right_layout)

        # Set the right pane inside the dockable widget
        dock_widget.setWidget(right_pane)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.music_player.clear_playlist()
            self.load_folder_tree(folder)

    def toggle_shuffle(self):
        self.music_player.shuffle_playlist()
        self.update_playlist_display()

    def toggle_repeat(self):
        # Example repeat functionality
        print("Toggled Repeat (You can implement actual logic here)")

    def load_folder_tree(self, folder_path):
        self.folder_tree = FolderTree(folder_path)
        # Populate the tree view with folder structure (implementation depends on FolderTree class)

    def update_playlist_display(self):
        self.playlist_box.clear()
        for song in self.music_player.playlist:
            self.playlist_box.addItem(song)

    def toggle_play_pause(self):
        if self.music_player.is_playing:
            self.music_player.pause_music()
        else:
            self.music_player.play_music()

    def stop_music(self):
        self.music_player.stop_music()
