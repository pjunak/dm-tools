import os
import tkinter as tk
from tkinter import ttk, filedialog, Listbox, Menu
from music_player import MusicPlayer
from folder_tree import FolderTree
from typing import Optional

class DMToolsUI:
    def __init__(self, root: tk.Tk, debug: bool = False) -> None:
        self.root = root
        self.root.title("Dungeon Master Music Player")
        self.root.geometry("800x400")
        self.debug = debug

        # Music player
        self.music_player = MusicPlayer(debug=self.debug)
        self.is_playing = False  # Track if the music is currently playing or paused
        self.is_paused = False   # Track if the music is paused

        # Add menu to the UI
        self.create_menu()

        # Initialize with no folder loaded
        self.root_dir = None

        # UI setup without a folder preloaded
        self.setup_ui()

    def create_menu(self) -> None:
        """Create a top menu with direct Folder, Settings, Extensions, and Creator options."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # Direct Folder Button (No nested menu)
        menubar.add_command(label="Open Folder", command=self.open_folder)

        # Settings Menu
        settings_menu = Menu(menubar, tearoff=0)
        
        # Shuffle option
        self.shuffle_var = tk.BooleanVar(value=False)
        settings_menu.add_checkbutton(label="Shuffle", variable=self.shuffle_var, command=self.toggle_shuffle)
        
        # Repeat options
        repeat_menu = Menu(settings_menu, tearoff=0)
        self.repeat_mode = tk.StringVar(value="none")  # Default repeat mode
        repeat_menu.add_radiobutton(label="Repeat All", variable=self.repeat_mode, value="all")
        repeat_menu.add_radiobutton(label="Repeat One", variable=self.repeat_mode, value="one")
        repeat_menu.add_radiobutton(label="No Repeat", variable=self.repeat_mode, value="none")
        settings_menu.add_cascade(label="Repeat", menu=repeat_menu)

        menubar.add_cascade(label="Settings", menu=settings_menu)

        # Extensions Menu (Empty for now)
        extensions_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extensions", menu=extensions_menu)

        # Creator Menu (Empty for now)
        creator_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Creator", menu=creator_menu)

    def open_folder(self) -> None:
        """Open a folder, stop the current song, and load its contents into the folder tree."""
        self.log_debug("Open Folder button pressed.")
        self.root_dir = filedialog.askdirectory(title="Select Folder")
        
        if self.root_dir:
            self.log_debug(f"Folder selected: {self.root_dir}")
            self.stop_music()  # Stop any currently playing song
            self.music_player.clear_playlist()  # Clear the playlist when new folder is selected
            self.reload_folder_tree(self.root_dir)

    def toggle_shuffle(self) -> None:
        """Toggle shuffle mode on/off."""
        self.log_debug(f"Shuffle toggled: {self.shuffle_var.get()}")
        if self.shuffle_var.get():
            self.music_player.shuffle_playlist()
        self.update_playlist_display()

    def setup_ui(self) -> None:
        """Set up the folder tree and playlist UI components."""
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill='both')

        # Tree view with scrollbar (left side for selecting folder)
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(side='left', padx=10, pady=10, fill='y')

        self.tree_view = ttk.Treeview(tree_frame)
        tree_scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=self.tree_view.yview)
        self.tree_view.configure(yscrollcommand=tree_scrollbar.set)
        self.tree_view.pack(side="left", fill='both', expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Playlist view with scrollbar (right side)
        playlist_frame = tk.Frame(main_frame)
        playlist_frame.pack(side='left', padx=10, pady=10, fill='y')

        self.playlist_box = Listbox(playlist_frame, height=20, width=40)
        playlist_scrollbar = tk.Scrollbar(playlist_frame, orient="vertical", command=self.playlist_box.yview)
        self.playlist_box.configure(yscrollcommand=playlist_scrollbar.set)
        self.playlist_box.pack(side="left", fill='both', expand=True)
        playlist_scrollbar.pack(side="right", fill="y")

        # Control buttons always visible (at the bottom of the window)
        control_frame = tk.Frame(self.root)
        control_frame.pack(side='bottom', padx=10, pady=10)

        # Combined Play/Pause Button
        self.play_pause_button = tk.Button(control_frame, text="Play", command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=0, padx=10)

        stop_button = tk.Button(control_frame, text="Stop", command=self.stop_music)
        stop_button.grid(row=0, column=1, padx=10)

        # Bind double-click event to the playlist for song selection
        self.playlist_box.bind("<Double-1>", self.on_song_double_click)
        
        # Bind double-click event to folder tree for opening playlists
        self.tree_view.bind("<Double-1>", self.on_folder_double_click)

    def reload_folder_tree(self, folder_path: str) -> None:
        """Reload the folder tree structure based on the new root folder."""
        self.log_debug(f"Reloading folder tree: {folder_path}")
        self.folder_tree = FolderTree(folder_path)
        
        # Clear and rebuild the folder tree
        self.tree_view.delete(*self.tree_view.get_children())
        for subtree in self.folder_tree.tree['folders']:
            if os.listdir(subtree['path']) and os.path.basename(subtree['path']):  # Ensure valid folder
                self.populate_tree(self.tree_view, subtree)

    def on_folder_double_click(self, event: tk.Event) -> None:
        """Load playlist from the selected folder in the folder tree."""
        try:
            item = self.tree_view.selection()[0]  # Ensure something is selected
            folder_path = self.tree_view.item(item, 'values')[0]

            if os.path.isdir(folder_path):
                self.log_debug(f"Folder double-clicked: {folder_path}")
                self.stop_music()  # Stop current song if a new folder is double-clicked
                self.music_player.clear_playlist()  # Clear playlist on folder switch
                self.music_player.load_playlist(folder_path)
                self.update_playlist_display()
        except IndexError:
            self.log_debug("No folder selected for double-click.")

    def populate_tree(self, tree_view: ttk.Treeview, tree_data: dict, parent: str = '') -> None:
        """Populate the folder tree with subdirectories."""
        node_tag = 'leaf' if tree_data['is_leaf'] else 'non-leaf'
        node = tree_view.insert(parent, 'end', text=os.path.basename(tree_data['path']), values=[tree_data['path']], tags=(node_tag,))
        
        if not tree_data['is_leaf']:
            for subtree in tree_data['folders']:
                self.populate_tree(self.tree_view, subtree, node)

    def on_song_double_click(self, event: tk.Event) -> None:
        """Play the selected song when double-clicked in the playlist."""
        selected_idx = self.playlist_box.curselection()
        if selected_idx:
            song_idx = selected_idx[0]
            self.stop_music()  # Stop any currently playing song
            self.music_player.play_from_index(song_idx)  # Play the song from the selected index
            self.is_playing = True
            self.is_paused = False
            self.play_pause_button.config(text="Pause")
            self.update_playlist_display()

    def update_playlist_display(self) -> None:
        """Update the playlist view with the current playlist and highlight the current song."""
        self.playlist_box.delete(0, tk.END)
        for idx, song in enumerate(self.music_player.playlist):
            self.playlist_box.insert(tk.END, os.path.basename(song))

        if self.music_player.current_song:
            try:
                current_index = self.music_player.playlist.index(self.music_player.current_song)
                self.playlist_box.itemconfig(current_index, bg='yellow')
            except ValueError:
                pass  # If the song isn't in the playlist, skip highlighting

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if not self.music_player.playlist:
            self.log_debug("No playlist loaded.")
            print("No playlist loaded.")
            return

        if self.is_playing and not self.is_paused:
            self.music_player.pause_music()  # Pause the song
            self.is_paused = True
            self.play_pause_button.config(text="Play")
            self.log_debug("Music paused.")
        elif self.is_paused:
            self.music_player.resume_music()  # Resume the song
            self.is_paused = False
            self.play_pause_button.config(text="Pause")
            self.log_debug("Music resumed.")
        else:
            self.start_playback()  # Start playback if it's not playing

    def start_playback(self) -> None:
        """Start playing the selected song, or the first song if none selected."""
        selected_idx = self.playlist_box.curselection()
        if not selected_idx:
            selected_idx = [0]  # Default to the first song if nothing is selected
            self.playlist_box.select_set(0)  # Select the first song in the playlist
        song_idx = selected_idx[0]
        self.music_player.play_from_index(song_idx)
        self.is_playing = True
        self.is_paused = False
        self.play_pause_button.config(text="Pause")
        self.update_playlist_display()

    def stop_music(self) -> None:
        """Stop the music and reset the playlist state."""
        self.music_player.stop_music()
        self.is_playing = False
        self.is_paused = False
        self.play_pause_button.config(text="Play")
        self.update_playlist_display()
        self.log_debug("Music stopped.")

    def log_debug(self, message: str) -> None:
        """Helper to log debug messages if in debug mode."""
        if self.debug:
            print(f"DEBUG: {message}")
