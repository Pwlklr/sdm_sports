from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FootballMatchConfig:
    """Defines the format of a football match for a specific tournament phase."""

    number_of_halves: int = 2
    half_length_minutes: int = 45
    allow_draw: bool = True
    extra_time_halves: int = 2
    extra_time_half_length: int = 15
    penalty_shootout_rounds: int = 5
    yellows_per_dismissal: int = 2
    golden_goal: bool = False
    players_on_pitch: int = 11
    min_players_on_pitch: int = 7
    max_substitutions: int = 5

    @classmethod
    def fifa(cls) -> FootballMatchConfig:
        """Standard knockout match: 2x45, extra time and penalties, no draw."""
        return cls(allow_draw=False)

    @classmethod
    def league(cls) -> FootballMatchConfig:
        """League match: draws allowed, no extra time or penalties."""
        return cls(allow_draw=True, extra_time_halves=0)

    @classmethod
    def cup(cls) -> FootballMatchConfig:
        """Cup match: no draw, golden goal in extra time."""
        return cls(allow_draw=False, golden_goal=True)
