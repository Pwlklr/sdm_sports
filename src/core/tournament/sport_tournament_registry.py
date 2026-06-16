from __future__ import annotations

from collections.abc import Callable

from src.core.tournament.sport_tournament_profile import SportTournamentProfile

ProfileBuilder = Callable[[], SportTournamentProfile]


class SportTournamentRegistry:
    _builders: dict[str, ProfileBuilder] = {}

    @classmethod
    def register(cls, sport_id: str, builder: ProfileBuilder) -> None:
        if sport_id in cls._builders:
            raise ValueError(f"Tournament profile already registered for '{sport_id}'")
        cls._builders[sport_id] = builder

    @classmethod
    def get(cls, sport_id: str) -> SportTournamentProfile:
        builder = cls._builders.get(sport_id)
        if builder is None:
            raise ValueError(f"No tournament profile registered for sport '{sport_id}'")
        return builder()
