from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DartsMatchConfig:
    starting_score: int = 501
    legs_to_win_set: int = 3
    sets_to_win_match: int = 2
    in_multiplier: int = 1
    out_multiplier: int = 2
    darts_per_turn: int = 3

    @classmethod
    def standard_501(cls) -> DartsMatchConfig:
        """Classic 501, double-out, best of 5 sets x 3 legs."""
        return cls(
            starting_score=501,
            legs_to_win_set=3,
            sets_to_win_match=3,
            in_multiplier=1,
            out_multiplier=2,
        )

    @classmethod
    def quick_301(cls) -> DartsMatchConfig:
        """Short 301, single set, straight in/out."""
        return cls(
            starting_score=301,
            legs_to_win_set=3,
            sets_to_win_match=1,
            in_multiplier=1,
            out_multiplier=1,
        )
