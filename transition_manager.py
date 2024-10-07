class TransitionManager:
    def __init__(self) -> None:
        self.transitions = {}

    def add_transition(self, name: str, transition) -> None:
        """Add a new transition by name."""
        self.transitions[name] = transition

    def get_transition(self, name: str):
        """Retrieve a transition by name."""
        return self.transitions.get(name)

    def remove_transition(self, name: str) -> None:
        """Remove a transition by name."""
        if name in self.transitions:
            del self.transitions[name]
