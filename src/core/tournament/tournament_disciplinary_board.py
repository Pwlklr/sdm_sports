from typing import Iterable

from src.core.contestant.models import Contestant


class TournamentDisciplinaryBoard:
    """Tracks tournament-wide infractions and the resulting match suspensions."""

    def __init__(self) -> None:
        self.records: dict[str, list[str]] = {}
        self.suspensions: dict[str, int] = {}

    def log_infraction(self, contestant: Contestant, infraction: str) -> None:
        self.records.setdefault(contestant.id, []).append(infraction)

    def log_infraction_id(self, player_id: str, infraction: str) -> None:
        self.records.setdefault(player_id, []).append(infraction)

    def infraction_count(self, player_id: str, infraction: str) -> int:
        return self.records.get(player_id, []).count(infraction)

    def suspend(self, player_id: str, matches: int = 1) -> None:
        self.suspensions[player_id] = max(self.suspensions.get(player_id, 0), matches)

    def is_suspended(self, player_id: str) -> bool:
        return self.suspensions.get(player_id, 0) > 0

    def suspended_ids(self) -> frozenset[str]:
        return frozenset(
            player_id for player_id, matches in self.suspensions.items() if matches > 0
        )

    def serve_match(self, player_ids: Iterable[str]) -> None:
        """Decrement remaining suspension for players who sat out a match."""
        for player_id in player_ids:
            remaining = self.suspensions.get(player_id, 0)
            if remaining > 0:
                self.suspensions[player_id] = remaining - 1

    def amnesty(self) -> None:
        """Clear accumulated cautions and suspensions (e.g. after a tournament phase)."""
        self.records.clear()
        self.suspensions.clear()
