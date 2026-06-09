from dataclasses import dataclass


@dataclass(frozen=True)
class DartsMatchConfig:
    starting_score: int = 501
    legs_to_win_set: int = 3
    sets_to_win_match: int = 2
    in_multiplier: int = 1
    out_multiplier: int = 2
    darts_per_turn: int = 3
