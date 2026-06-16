from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.event import OfficialOverrideEvent, ProjectionEvent
from src.sports.football.contest.entities import PeriodKind


@dataclass(frozen=True, kw_only=True)
class FootballEvent(ProjectionEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class MatchStarted(FootballEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class PeriodStarted(FootballEvent):
    kind: PeriodKind
    index: int


@dataclass(frozen=True, kw_only=True)
class GoalScored(FootballEvent):
    team_id: str
    minute: int
    scorer_id: str | None = None
    own_goal: bool = False
    penalty: bool = False


@dataclass(frozen=True, kw_only=True)
class PlayerCautioned(FootballEvent):
    team_id: str
    offender_id: str
    minute: int


@dataclass(frozen=True, kw_only=True)
class PlayerDismissed(FootballEvent):
    team_id: str
    offender_id: str
    minute: int


@dataclass(frozen=True, kw_only=True)
class PeriodEnded(FootballEvent):
    kind: PeriodKind


@dataclass(frozen=True, kw_only=True)
class ExtraTimeStarted(FootballEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class PenaltyShootoutStarted(FootballEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class PenaltyKickTaken(FootballEvent):
    team_id: str
    scored: bool


@dataclass(frozen=True, kw_only=True)
class MatchConcluded(FootballEvent):
    winner_id: str | None = None
    draw: bool = False
    decided_by: str = "regulation"


@dataclass(frozen=True, kw_only=True)
class LineupSubmitted(FootballEvent):
    team_id: str
    starting: tuple[str, ...]
    bench: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class PlayerSubstituted(FootballEvent):
    team_id: str
    player_out: str
    player_in: str
    minute: int


@dataclass(frozen=True, kw_only=True)
class GoalScorerCorrected(FootballEvent):
    goal_event_id: str
    team_id: str
    minute: int
    previous_scorer_id: str
    new_scorer_id: str


@dataclass(frozen=True, kw_only=True)
class ContestResultOverridden(OfficialOverrideEvent):
    winner_id: str
    reason: str
    winner_score: int = 3
    loser_score: int = 0
