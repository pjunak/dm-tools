import os
import customtkinter as ctk
from tkinter import filedialog, ttk, Scrollbar, Listbox
import tkinter as tk  # Import tkinter for standard widgets
from music_player import MusicPlayer
from folder_tree import FolderTree

class DMToolsUI:
    def __init__(self, root: ctk.CTk, debug: bool = False) -> None:
        self.root = root
        self.root.title("Dungeon Master Music Player")

        # Set the window size dynamically based on screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        window_position_x = int((screen_width - window_width) / 2)
        window_position_y = int((screen_height - window_height) / 2)

        self.root.geometry(f"{window_width}x{window_height}+{window_position_x}+{window_position_y}")

        # Set dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Apply a dark style to the Treeview, Scrollbars, and top menu
        self.apply_dark_mode()

        self.debug = debug

        # Music player
        self.music_player = MusicPlayer(debug=self.debug)
        self.is_playing = False
        self.is_paused = False

        # Add menu to the UI
        self.create_menu()

        # Initialize with no folder loaded
        self.root_dir = None

        # UI setup without a folder preloaded
        self.setup_ui()

    def apply_dark_mode(self) -> None:
        """Applies a dark mode style to the Treeview, scrollbars, and top menu."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2e2e2e", foreground="white", fieldbackground="#2e2e2e", highlightthickness=0, borderwidth=0)
        style.configure("Treeview.Heading", background="#3e3e3e", foreground="white")
        style.map("Treeview", background=[('selected', '#3e3e3e')], foreground=[('selected', 'white')])
        style.configure("Vertical.TScrollbar", troughcolor="#2e2e2e", background="#3e3e3e", arrowcolor="white")
        style.configure("Horizontal.TScrollbar", troughcolor="#2e2e2e", background="#3e3e3e", arrowcolor="white")

    def create_menu(self) -> None:
        # Creating a dark background for the top menu and restoring missing buttons
        menubar = tk.Menu(self.root, bg="#2e2e2e", fg="white", activebackground="#3e3e3e", activeforeground="white", bd=0, relief="flat")
        self.root.config(menu=menubar)

        menubar.add_command(label="Open Folder", command=self.open_folder)

        # Settings menu restored with missing buttons
        settings_menu = tk.Menu(menubar, tearoff=0, bg="#2e2e2e", fg="white", activebackground="#3e3e3e", activeforeground="white", bd=0, relief="flat")
        self.shuffle_var = ctk.BooleanVar(value=False)
        settings_menu.add_checkbutton(label="Shuffle", variable=self.shuffle_var, command=self.toggle_shuffle)
        repeat_menu = tk.Menu(settings_menu, tearoff=0, bg="#2e2e2e", fg="white", activebackground="#3e3e3e", activeforeground="white")
        self.repeat_mode = ctk.StringVar(value="none")
        repeat_menu.add_radiobutton(label="Repeat All", variable=self.repeat_mode, value="all")
        repeat_menu.add_radiobutton(label="Repeat One", variable=self.repeat_mode, value="one")
        repeat_menu.add_radiobutton(label="No Repeat", variable=self.repeat_mode, value="none")
        settings_menu.add_cascade(label="Repeat", menu=repeat_menu)

        # Restoring missing buttons in the top menu
        menubar.add_command(label="Play", command=self.toggle_play_pause)
        menubar.add_command(label="Stop", command=self.stop_music)
        menubar.add_command(label="Exit", command=self.root.quit)

        menubar.add_cascade(label="Settings", menu=settings_menu)

    def open_folder(self) -> None:
        self.root_dir = filedialog.askdirectory(title="Select Folder")
        if self.root_dir:
            self.stop_music()
            self.music_player.clear_playlist()
            self.reload_folder_tree(self.root_dir)

    def toggle_shuffle(self) -> None:
        if self.shuffle_var.get():
            self.music_player.shuffle_playlist()
        self.update_playlist_display()

    def setup_ui(self) -> None:
        # Create a PanedWindow to hold the resizable panes
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg="#2e2e2e")  # Sashwidth controls the width of the splitter
        paned_window.pack(fill="both", expand=True)

        # Left Pane: Treeview
        tree_frame = ctk.CTkFrame(paned_window, fg_color="#2e2e2e")
        paned_window.add(tree_frame)  # Add Treeview pane to the paned window

        self.tree_view = ttk.Treeview(tree_frame)
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_view.yview)
        self.tree_view.configure(yscrollcommand=tree_scrollbar.set)

        self.tree_view.pack(side="left", fill='both', expand=True)
        tree_scrollbar.pack(side="left", fill="y")

        # Right Pane: Playlist and control buttons
        playlist_control_frame = ctk.CTkFrame(paned_window, fg_color="#2e2e2e")
        paned_window.add(playlist_control_frame, minsize=200)  # The right pane is now expandable/retractable

        playlist_frame = ctk.CTkFrame(playlist_control_frame, fg_color="#2e2e2e")
        playlist_frame.pack(side='top', padx=10, pady=10, fill='y')

        self.playlist_box = Listbox(playlist_frame, height=20, width=40, bg="#2e2e2e", fg="white", selectbackground="#3e3e3e", selectforeground="white")
        playlist_scrollbar = ttk.Scrollbar(playlist_frame, orient="vertical", command=self.playlist_box.yview)
        self.playlist_box.configure(yscrollcommand=playlist_scrollbar.set)
        self.playlist_box.pack(side="left", fill='both', expand=True)
        playlist_scrollbar.pack(side="right", fill="y")

        # Control buttons at the bottom of the right pane
        control_frame = ctk.CTkFrame(playlist_control_frame, fg_color="#2e2e2e")
        control_frame.pack(side='bottom', padx=10, pady=10)

        self.play_pause_button = ctk.CTkButton(control_frame, text="Play", command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=0, padx=10)

        stop_button = ctk.CTkButton(control_frame, text="Stop", command=self.stop_music)
        stop_button.grid(row=0, column=1, padx=10)

        # Bind events to the Treeview and Playlist
        self.playlist_box.bind("<Double-1>", self.on_song_double_click)
        self.tree_view.bind("<Double-1>", self.on_folder_double_click)





    def reload_folder_tree(self, folder_path: str) -> None:
        self.folder_tree = FolderTree(folder_path)
        self.tree_view.delete(*self.tree_view.get_children())
        for subtree in self.folder_tree.tree['folders']:
            if os.listdir(subtree['path']) and os.path.basename(subtree['path']):
                self.populate_tree(self.tree_view, subtree)

    def populate_tree(self, tree_view: ttk.Treeview, tree_data: dict, parent: str = '') -> None:
        node_tag = 'leaf' if tree_data['is_leaf'] else 'non-leaf'
        node = tree_view.insert(parent, 'end', text=os.path.basename(tree_data['path']), values=[tree_data['path']], tags=(node_tag,))
        if not tree_data['is_leaf']:
            for subtree in tree_data['folders']:
                self.populate_tree(self.tree_view, subtree, node)

    def on_folder_double_click(self, event: tk.Event) -> None:
        selected_item = self.tree_view.selection()
        if selected_item:
            folder_path = self.tree_view.item(selected_item[0], "values")[0]
            self.reload_folder_tree(folder_path)

    def on_song_double_click(self, event: tk.Event) -> None:
        selected_idx = self.playlist_box.curselection()
        if selected_idx:
            song_idx = selected_idx[0]
            self.stop_music()
            self.music_player.play_from_index(song_idx)
            self.is_playing = True
            self.is_paused = False
            self.play_pause_button.configure(text="Pause")  # Use configure instead of config
            self.update_playlist_display()

    def update_playlist_display(self) -> None:
        self.playlist_box.delete(0, tk.END)
        for idx, song in enumerate(self.music_player.playlist):
            self.playlist_box.insert(tk.END, os.path.basename(song))
        if self.music_player.current_song:
            try:
                current_index = self.music_player.playlist.index(self.music_player.current_song)
                self.playlist_box.itemconfig(current_index, bg='yellow')
            except ValueError:
                pass

    def stop_music(self) -> None:
        """Stop the music and reset the playback state."""
        self.music_player.stop_music()
        self.is_playing = False
        self.is_paused = False
        self.play_pause_button.configure(text="Play")  # Use configure instead of config
        self.update_playlist_display()

    def toggle_play_pause(self) -> None:
        if not self.music_player.playlist:
            return
        if self.is_playing and not self.is_paused:
            self.music_player.pause_music()
            self.is_paused = True
            self.play_pause_button.configure(text="Play")  # Use configure instead of config
        elif self.is_paused:
            self.music_player.resume_music()
            self.is_paused = False
            self.play_pause_button.configure(text="Pause")  # Use configure instead of config
        else:
            self.start_playback()

    def start_playback(self) -> None:
        selected_idx = self.playlist_box.curselection()
        if not selected_idx:
            selected_idx = [0]
            self.playlist_box.select_set(0)
        song_idx = selected_idx[0]
        self.music_player.play_from_index(song_idx)
        self.is_playing = True
        self.is_paused = False
        self.play_pause_button.configure(text="Pause")  # Use configure instead of config
        self.update_playlist_display()
