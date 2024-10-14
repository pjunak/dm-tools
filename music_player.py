import os
import pygame
import threading
import random
import logging
from datetime import datetime
from typing import Optional

class MusicPlayer:
    def __init__(self, debug: bool = False):
        self.playlist = []
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.debug = debug  # Add this to initialize the debug attribute
        self.logger = logging.getLogger('DMTools.MusicPlayer')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)


    def setup_logging(self) -> None:
        if not os.path.exists('log'):
            os.makedirs('log')

        log_filename = datetime.now().strftime("log/%Y-%m-%d_%H-%M-%S.log")
        logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def log(self, message: str) -> None:
        """Log messages based on debug mode."""
        if self.debug:
            self.logger.debug(message)
        else:
            self.logger.info(message)

    def load_playlist(self, folder_path: str) -> None:
        """Load a playlist from the given folder path."""
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
        """Play the currently selected song."""
        if self.current_song:
            self.stop_event.clear()  # Reset stop event before playing
            try:
                self.log(f"Trying to play {self.current_song}")
                pygame.mixer.music.load(self.current_song)
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused = False
                self.log(f"Playing {self.current_song}")
            except Exception as e:
                self.log(f"Error playing {self.current_song}: {e}")
                print(f"Error playing {self.current_song}: {e}")

    def play_from_index(self, index: int) -> None:
        """Play the song from the selected index."""
        if 0 <= index < len(self.playlist):
            self.current_index = index  # Update index
            self.current_song = self.playlist[self.current_index]  # Set the current song
            self.play()  # Play the selected song

    def play_next_song(self) -> None:
        """Play the next song from the playlist."""
        self.current_index = (self.current_index + 1) % len(self.playlist)  # Loop back to start if at the end
        self.current_song = self.playlist[self.current_index]  # Update the current song
        self.play()  # Play the next song

    def stop_music(self) -> None:
        """Stop the music playback."""
        if self.is_playing or self.is_paused:
            self.stop_event.set()  # Signal to stop the control thread
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_song = None  # Clear the current song after stopping
            self.log("Stopped music playback.")
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join()

    def pause_music(self) -> None:
        """Pause the currently playing song."""
        if self.is_playing and pygame.mixer.music.get_busy():
            self.pause_event.set()  # Set pause event to stop playback
            pygame.mixer.music.pause()
            self.is_paused = True

    def resume_music(self) -> None:
        """Resume the paused song."""
        if self.is_paused:
            self.pause_event.clear()  # Clear pause event to resume playback
            pygame.mixer.music.unpause()
            self.is_paused = False

    def skip_to_next_song(self) -> None:
        """Signal to skip to the next song."""
        if self.is_playing:
            self.next_song_event.set()
            self.log("Skipping to next song.")

    def shuffle_playlist(self) -> None:
        """Shuffle the playlist without interrupting the current song."""
        current_song = self.current_song
        random.shuffle(self.playlist)
        if current_song:
            # Ensure the current song stays at the current position
            self.current_index = self.playlist.index(current_song)

    def clear_playlist(self) -> None:
        """Clear the current playlist and reset the state."""
        self.log("Clearing playlist.")
        self.playlist = []
        self.current_song = None
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
