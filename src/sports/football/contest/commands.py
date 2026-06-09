from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command


@dataclass(frozen=True, kw_only=True)
class StartMatch(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class ScoreGoal(Command):
    team_index: int
    minute: int
    scorer_id: str | None = None
    own_goal: bool = False
    penalty: bool = False


@dataclass(frozen=True, kw_only=True)
class CommitFoul(Command):
    team_index: int
    minute: int
    card: str | None = None
    offender_id: str | None = None
    reason: str = "Foul play"


@dataclass(frozen=True, kw_only=True)
class EndPeriod(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class TakePenaltyKick(Command):
    team_index: int
    scored: bool
