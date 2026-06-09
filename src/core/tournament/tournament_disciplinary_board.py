from src.core.contestant.models import Contestant


class TournamentDisciplinaryBoard:
    """Tracks tournament-wide infractions across matches."""

    def __init__(self) -> None:
        self.records: dict[str, list[str]] = {}

    def log_infraction(self, contestant: Contestant, infraction: str) -> None:
        if contestant.id not in self.records:
            self.records[contestant.id] = []
        self.records[contestant.id].append(infraction)
