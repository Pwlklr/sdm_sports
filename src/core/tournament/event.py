from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contest.contest import Contest
    from src.core.contestant.models import Contestant
    from src.core.contest.result import Result


class TournamentEvent(ABC):
    """Base class for all tournament-level domain events."""

    pass


class RegistrationOpened(TournamentEvent):
    pass


class PlayerRegistered(TournamentEvent):
    def __init__(self, contestant: "Contestant") -> None:
        self.contestant = contestant


class RegistrationClosed(TournamentEvent):
    pass


class MatchScheduled(TournamentEvent):
    def __init__(self, match: "Contest") -> None:
        self.match = match


class MatchCompleted(TournamentEvent):
    def __init__(self, match: "Contest", result: "Result | None" = None) -> None:
        self.match = match
        self.result = result


class PhaseCompleted(TournamentEvent):
    def __init__(self, phase_name: str, qualifiers: list["Contestant"]) -> None:
        self.phase_name = phase_name
        self.qualifiers = qualifiers
