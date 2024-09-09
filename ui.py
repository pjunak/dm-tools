import tkinter as tk
from tkinter import ttk, filedialog
from music_player import MusicPlayer
from folder_tree import FolderTree
import os

class DMToolsUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dungeon Master Music Player")
        self.root.geometry("600x400")

        # Get the current directory of the script
        current_directory = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(current_directory, 'media'+'\\'+'icon.png')

        # Set the window icon
        icon_image = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(False, icon_image)

        # Folder selector dialog
        self.root_dir = filedialog.askdirectory(title="Select Root Music Folder")
        if not self.root_dir:
            print("No folder selected. Exiting program.")
            self.root.destroy()
            return

        self.music_player = MusicPlayer()
        self.folder_tree = FolderTree(self.root_dir)

        self.setup_ui()

    def setup_ui(self):
        self.tree_view = ttk.Treeview(self.root)
        for subtree in self.folder_tree.tree['folders']:
            self.populate_tree(self.tree_view, subtree)
        self.tree_view.pack(expand=True, fill='both')
        self.tree_view.bind("<Double-1>", self.on_folder_double_click)

        self.current_song_label = tk.Label(self.root, text="Current Song: None")
        self.current_song_label.pack()

        stop_button = tk.Button(self.root, text="Stop Music", command=self.stop_music)
        stop_button.pack(side=tk.LEFT)

        next_song_button = tk.Button(self.root, text="Next Song", command=self.play_next_song)
        next_song_button.pack(side=tk.LEFT)


    def populate_tree(self, tree_view, tree_data, parent=''):
        # Check if the folder is a leaf folder and tag it accordingly
        node_tag = 'leaf' if tree_data['is_leaf'] else 'non-leaf'
        node = tree_view.insert(parent, 'end', text=os.path.basename(tree_data['path']), values=[tree_data['path']], tags=(node_tag,))
        
        if not tree_data['is_leaf']:
            for subtree in tree_data['folders']:
                self.populate_tree(tree_view, subtree, node)

    def on_folder_double_click(self, event):
        item = self.tree_view.selection()[0]
        folder_path = self.tree_view.item(item, 'values')[0]

        # Check if the selected item is a leaf or non-leaf folder
        if self.tree_view.item(item, 'values'):
            # Leaf folder logic
            if self.music_player.is_playing:
                self.music_player.stop_music()

            self.music_player.load_playlist(folder_path)
            self.music_player.play_music_loop()
            self.update_current_song_label()
        else:
            # Non-leaf folder logic - toggle expansion/collapse
            if self.tree_view.item(item, 'open'):
                self.tree_view.item(item, open=False)
            else:
                self.tree_view.item(item, open=True)

    def play_music_from_folder(self, folder_path):
        """Play music from the selected folder."""
        # Stop current music only if it's playing
        if self.music_player.is_playing:
            self.music_player.stop_music()

        self.music_player.load_playlist(folder_path)
        self.music_player.play_music_loop()
        self.update_current_song_label()

    def play_next_song(self):
        if self.music_player.playlist:
            # Skip to the next song using the non-blocking method
            self.music_player.skip_to_next_song()
            self.update_current_song_label()
        else:
            self.current_song_label.config(text="No more songs in the playlist.")

    def update_current_song_label(self):
        if self.music_player.current_song:
            current_song = os.path.basename(self.music_player.current_song)
            self.current_song_label.config(text=f"Current Song: {current_song}")
        else:
            self.current_song_label.config(text="Current Song: None")

    def stop_music(self):
        self.music_player.stop_music()
        self.current_song_label.config(text="Current Song: None")