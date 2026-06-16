from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.core.contest.contest_result import ContestResult


@dataclass(frozen=True, kw_only=True)
class TournamentCommand:
    """Immutable intent issued against a tournament."""

    issued_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, kw_only=True)
class OpenRegistration(TournamentCommand):
    pass


@dataclass(frozen=True, kw_only=True)
class RegisterContestant(TournamentCommand):
    contestant_id: str
    contestant_name: str


@dataclass(frozen=True, kw_only=True)
class RegisterSquad(TournamentCommand):
    contestant_id: str
    player_ids: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class CloseRegistration(TournamentCommand):
    pass


@dataclass(frozen=True, kw_only=True)
class StartPhase(TournamentCommand):
    phase_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class ScheduleFixtures(TournamentCommand):
    phase_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class RecordMatchOutcome(TournamentCommand):
    contest_id: str
    result: ContestResult


@dataclass(frozen=True, kw_only=True)
class CorrectMatchOutcome(TournamentCommand):
    contest_id: str
    result: ContestResult


@dataclass(frozen=True, kw_only=True)
class PerformDraw(TournamentCommand):
    phase_id: str | None = None
    method: str = "random"


@dataclass(frozen=True, kw_only=True)
class RegisterContestantRef(TournamentCommand):
    """Carries full contestant reference for registration (application layer)."""

    contestant: Any


@dataclass(frozen=True, kw_only=True)
class IssueSuspension(TournamentCommand):
    """Admin command: manually suspend a player for a number of matches."""

    player_id: str
    matches: int = 1


@dataclass(frozen=True, kw_only=True)
class LiftSuspension(TournamentCommand):
    """Admin command: clear a player's remaining suspension."""

    player_id: str
