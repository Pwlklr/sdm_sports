from __future__ import annotations

from dataclasses import dataclass

from src.core.event import Event
from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot
from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.scheduling_mode import SchedulingMode


@dataclass(frozen=True, kw_only=True)
class TournamentEvent(Event):
    """Base class for all tournament-level domain events."""


@dataclass(frozen=True, kw_only=True)
class TournamentProjectionEvent(TournamentEvent):
    """Fact that mutates tournament state via apply()."""


@dataclass(frozen=True, kw_only=True)
class RegistrationOpened(TournamentProjectionEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class RegistrationClosed(TournamentProjectionEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class ContestantRegistered(TournamentProjectionEvent):
    contestant_id: str
    contestant_name: str


@dataclass(frozen=True, kw_only=True)
class PhaseStarted(TournamentProjectionEvent):
    phase_id: str
    phase_name: str
    format: PhaseFormat
    scheduling_mode: SchedulingMode


@dataclass(frozen=True, kw_only=True)
class FixtureScheduled(TournamentProjectionEvent):
    phase_id: str
    contest_id: str
    slot_id: str
    side_a_id: str
    side_b_id: str
    round_index: int = 0


@dataclass(frozen=True, kw_only=True)
class MatchOutcomeRecorded(TournamentProjectionEvent):
    phase_id: str
    snapshot: MatchOutcomeSnapshot


@dataclass(frozen=True, kw_only=True)
class RoundCompleted(TournamentProjectionEvent):
    phase_id: str
    round_index: int


@dataclass(frozen=True, kw_only=True)
class DrawPerformed(TournamentProjectionEvent):
    phase_id: str
    round_index: int
    pairings: tuple[tuple[str, str], ...]


@dataclass(frozen=True, kw_only=True)
class PhaseCompleted(TournamentProjectionEvent):
    phase_id: str
    qualifier_ids: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class SuspensionIssued(TournamentProjectionEvent):
    player_id: str
    matches: int


@dataclass(frozen=True, kw_only=True)
class TournamentCompleted(TournamentProjectionEvent):
    champion_id: str | None = None
