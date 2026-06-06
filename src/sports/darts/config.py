from dataclasses import dataclass

@dataclass(frozen=True)
class DartsMatchConfig:
    """Defines the format of a darts match for a specific tournament phase."""
    starting_score: int = 501
    legs_to_win_set: int = 3   # e.g., 3 means "Best of 5 legs"
    sets_to_win_match: int = 2 # e.g., 2 means "Best of 3 sets"