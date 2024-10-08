
import os
import pygame
import threading
import random
from datetime import datetime
from typing import Optional
from logging_utils import log_method_call, setup_logging

class MusicPlayer:
    def __init__(self, debug: bool = False) -> None:
        pygame.mixer.pre_init()
        pygame.mixer.init()
        self.playlist = []
        self.current_song = None
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.playback_thread = None
        self.stop_event = threading.Event()
        self.next_song_event = threading.Event()
        self.pause_event = threading.Event()
        setup_logging(debug=debug)

    @log_method_call
    def load_playlist(self, folder_path: str) -> None:
        try:
            all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.mp3')]
            random.shuffle(all_files)
            self.playlist = [os.path.normpath(song) for song in all_files]
            logging.debug(f"Loaded playlist with {len(self.playlist)} songs from {folder_path}")
        except Exception as e:
            logging.error(f"Error loading playlist: {e}")
            print(f"Error loading playlist: {e}")

    @log_method_call
    def play(self) -> None:
        if self.current_song:
            self.stop_event.clear()
            try:
                logging.debug(f"Trying to play {self.current_song}")
                pygame.mixer.music.load(self.current_song)
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused = False
                logging.info(f"Playing {self.current_song}")
            except Exception as e:
                logging.error(f"Error playing {self.current_song}: {e}")
                print(f"Error playing {self.current_song}: {e}")

    @log_method_call
    def play_from_index(self, index: int) -> None:
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.current_song = self.playlist[self.current_index]
            self.play()

    @log_method_call
    def play_next_song(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.current_song = self.playlist[self.current_index]
        self.play()

    @log_method_call
    def stop_music(self) -> None:
        if self.is_playing or self.is_paused:
            self.stop_event.set()
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_song = None
            logging.info("Stopped music playback.")
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join()

    @log_method_call
    def pause_music(self) -> None:
        if self.is_playing and pygame.mixer.music.get_busy():
            self.pause_event.set()
            pygame.mixer.music.pause()
            self.is_paused = True

    @log_method_call
    def resume_music(self) -> None:
        if self.is_paused:
            self.pause_event.clear()
            pygame.mixer.music.unpause()
            self.is_paused = False

    @log_method_call
    def skip_to_next_song(self) -> None:
        if self.is_playing:
            self.next_song_event.set()
            logging.debug("Skipping to next song.")

    @log_method_call
    def shuffle_playlist(self) -> None:
        current_song = self.current_song
        random.shuffle(self.playlist)
        if current_song:
            self.current_index = self.playlist.index(current_song)

    @log_method_call
    def clear_playlist(self) -> None:
        logging.debug("Clearing playlist.")
        self.playlist = []
        self.current_song = None
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
