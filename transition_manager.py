class TransitionManager:
    def __init__(self, music_player):
        self.music_player = music_player

    def transition_to_battle(self):
        """
        Transition to battle music.
        """
        # Load battle music playlist
        try:
            self.music_player.stop_music()
            self.music_player.load_playlist('path/to/battle_music_folder')
        except Exception as e:
            print('Error during transition to battle:', e)
        # Play battle music
        self.music_player.play_music_loop()

    def transition_to_calm(self):
        """
        Transition to calm music.
        """
        # Load calm music playlist
        try:
            self.music_player.stop_music()
            self.music_player.load_playlist('path/to/calm_music_folder')
        except Exception as e:
            print('Error during transition to calm:', e)
        # Play calm music
        self.music_player.play_music_loop()
