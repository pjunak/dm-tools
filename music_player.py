import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import threading
import random

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playlist = []
        self.current_song = None
        self.is_playing = False
        self.playback_thread = None

    def load_playlist(self, folder_path):
        """Load all music files from the specified folder into the playlist."""
        all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.mp3')]

        # Filter out intro songs and other songs
        intro_songs = [f for f in all_files if os.path.basename(f).lower().startswith('intro_')]
        other_songs = [f for f in all_files if f not in intro_songs]

        # Shuffle the non-intro songs
        random.shuffle(other_songs)

        # Prioritize intro songs, followed by the rest
        self.playlist = intro_songs + other_songs

    def play_music_loop(self):
        """Start music playback in a loop in a separate thread."""
        if not self.playlist:
            return

        if not self.is_playing or not self.playback_thread.is_alive():
            self.is_playing = True
            self.playback_thread = threading.Thread(target=self.play_next_song, daemon=True)
            self.playback_thread.start()

    def play_next_song(self):
        """Play the next song in the playlist. If the playlist is empty, stop the playback."""
        while self.playlist and self.is_playing:
            self.current_song = self.playlist.pop(0)
            try:
                pygame.mixer.music.load(self.current_song)
                pygame.mixer.music.play()

                # Wait for the music to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            except Exception as e:
                print(f"Error playing {self.current_song}: {e}")

    def skip_to_next_song(self):
        if self.playlist and self.is_playing:
            # Stop the current song
            pygame.mixer.music.stop()

            # Play the next song
            if self.playlist:
                self.current_song = self.playlist.pop(0)
                try:
                    pygame.mixer.music.load(self.current_song)
                    pygame.mixer.music.play()
                except Exception as e:
                    print(f"Error playing {self.current_song}: {e}")

    def stop_music(self):
        """Stop the music playback if it is playing."""
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join()
        # Clear the playlist and reset the current song
        self.playlist = []
        self.current_song = None
    