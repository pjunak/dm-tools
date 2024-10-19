import os
import pygame
import threading
import random
import logging
from datetime import datetime
from typing import Optional

class MusicPlayer:
    def __init__(self, debug=False):
        self.debug = debug
        self.playlist = []
        self.current_song_idx = 0
        self.is_playing = False
        self.is_paused = False
        self.stop_event = threading.Event()
        self.logger = logging.getLogger('DMTools.MusicPlayer')
        self.is_initialized = False
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        try:
            pygame.mixer.init()
            self.is_initialized = True
            self.logger.info("Pygame mixer initialized successfully.")
        except pygame.error as e:
            self.logger.error(f"Failed to initialize pygame mixer: {e}")
            self.is_initialized = False  # Mark initialization as failed

    def setup_logging(self) -> None:
        if not os.path.exists('log'):
            os.makedirs('log')

        log_filename = datetime.now().strftime("log/%Y-%m-%d_%H-%M-%S.log")
        logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def log(self, message: str) -> None:
        # Log messages based on debug mode.
        if self.debug:
            self.logger.debug(message)
        else:
            self.logger.info(message)

    def load_playlist(self, folder_path: str) -> None:
        # Load a playlist from the given folder path.
        if not self.is_initialized:
            self.logger.error("Pygame mixer not initialized. Cannot load playlist.")
            return
        try:
            if not os.path.isdir(folder_path):
                self.logger.error(f"Invalid folder path: {folder_path}")
                return
            self.playlist = []
            for file in os.listdir(folder_path):
                if file.endswith(".mp3") or file.endswith(".wav"):
                    full_path = os.path.join(folder_path, file)
                    self.playlist.append(full_path)
            self.logger.debug(f"Loaded playlist with {len(self.playlist)} songs from {folder_path}")
        except Exception as e:
            self.logger.error(f"Failed to load playlist: {e}")

    def play(self) -> None:
        if not self.is_initialized:
            self.logger.error("Pygame mixer is not initialized. Cannot play music.")
            return

        if self.current_song:
            self.stop_event.clear()
            try:
                self.log(f"Trying to play {self.current_song}")
                pygame.mixer.music.load(self.current_song)
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused = False
                self.log(f"Playing {self.current_song}")
            except pygame.error as e:
                self.log(f"Error playing {self.current_song}: {e}")

    def play_from_index(self, index: int) -> None:
        # Play the song from the selected index.
        if not self.is_initialized:
            self.logger.error("Pygame mixer not initialized. Cannot play from index.")
            return
        if 0 <= index < len(self.playlist):
            self.current_index = index  # Update index
            self.current_song = self.playlist[self.current_index]  # Set the current song
            self.play()  # Play the selected song

    def stop_music(self) -> None:
        # Stop the music playback.
        if not self.is_initialized:
            self.logger.error("Pygame mixer not initialized. Cannot stop music.")
            return
        if self.is_playing or self.is_paused:
            self.stop_event.set()  # Signal to stop the control thread
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_song = None  # Clear the current song after stopping
            self.log("Stopped music playback.")

    def pause_music(self) -> None:
        # Pause the currently playing song.
        if not self.is_initialized:
            self.logger.error("Pygame mixer not initialized. Cannot pause music.")
            return
        if self.is_playing and pygame.mixer.music.get_busy():
            self.pause_event.set()  # Set pause event to stop playback
            pygame.mixer.music.pause()
            self.is_paused = True

    def resume_music(self) -> None:
        # Resume the paused song.
        if not self.is_initialized:
            self.logger.error("Pygame mixer not initialized. Cannot resume music.")
            return
        if self.is_paused:
            self.pause_event.clear()  # Clear pause event to resume playback
            pygame.mixer.music.unpause()
            self.is_paused = False

    def shuffle_playlist(self) -> None:
        # Shuffle the playlist without interrupting the current song.
        if not self.is_initialized:
            self.logger.error("Pygame mixer not initialized. Cannot shuffle playlist.")
            return
        current_song = self.current_song
        random.shuffle(self.playlist)
        if current_song:
            # Ensure the current song stays at the current position
            self.current_index = self.playlist.index(current_song)

    def clear_playlist(self) -> None:
        # Clear the current playlist and reset the state.
        self.log("Clearing playlist.")
        self.playlist = []
        self.current_song = None
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
