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
