import logging

class TransitionManager:
    def __init__(self, logger=None):
        """Initialize the transition manager."""
        self.logger = logger or logging.getLogger('DMTools.TransitionManager')

    def fade_out(self, duration: int):
        """Simulate a fade-out effect for the given duration."""
        self.logger.debug(f"Fading out over {duration} milliseconds.")

    def fade_in(self, duration: int):
        """Simulate a fade-in effect for the given duration."""
        self.logger.debug(f"Fading in over {duration} milliseconds.")

    def crossfade(self, duration: int):
        """Simulate a crossfade effect for the given duration."""
        self.logger.debug(f"Crossfading over {duration} milliseconds.")
