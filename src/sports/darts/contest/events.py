from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.event import OfficialOverrideEvent, ProjectionEvent


@dataclass(frozen=True, kw_only=True)
class DartsEvent(ProjectionEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class MatchStarted(DartsEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class DartScored(DartsEvent):
    player_id: str
    sector: int
    multiplier: int
    points: int


@dataclass(frozen=True, kw_only=True)
class Busted(DartsEvent):
    player_id: str


@dataclass(frozen=True, kw_only=True)
class TurnEnded(DartsEvent):
    player_id: str


@dataclass(frozen=True, kw_only=True)
class LegWon(DartsEvent):
    player_id: str


@dataclass(frozen=True, kw_only=True)
class SetWon(DartsEvent):
    player_id: str


@dataclass(frozen=True, kw_only=True)
class LegStarted(DartsEvent):
    starting_player_id: str


@dataclass(frozen=True, kw_only=True)
class MatchConcluded(DartsEvent):
    winner_id: str
    decided_by: str = "regulation"


@dataclass(frozen=True, kw_only=True)
class ContestResultOverridden(OfficialOverrideEvent):
    winner_id: str
    reason: str
