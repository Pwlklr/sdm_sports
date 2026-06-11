from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command, ReverseDecision


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


@dataclass(frozen=True, kw_only=True)
class SubmitLineup(Command):
    team_index: int
    starting: tuple[str, ...]
    bench: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class SubstitutePlayer(Command):
    team_index: int
    player_out: str
    player_in: str
    minute: int


@dataclass(frozen=True, kw_only=True)
class VarOverturnGoal(ReverseDecision):
    pass


@dataclass(frozen=True, kw_only=True)
class RevokeCaution(ReverseDecision):
    pass
