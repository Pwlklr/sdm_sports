from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.core.contest_event import ContestEvent

if TYPE_CHECKING:
    from src.core.contestant import Contestant


class FootballEvent(ContestEvent):
    """Base class for all football-specific domain events."""

    pass


class MatchStarted(FootballEvent):
    pass


class PeriodStarted(FootballEvent):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label


class PeriodEnded(FootballEvent):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label


class GoalScoredEvent(FootballEvent):
    """Input event raised when a side scores (or concedes an own goal)."""

    def __init__(
        self,
        team: Contestant,
        scorer_id: Optional[str] = None,
        minute: Optional[int] = None,
        own_goal: bool = False,
        penalty: bool = False,
    ) -> None:
        super().__init__()
        self.team = team
        self.scorer_id = scorer_id
        self.minute = minute
        self.own_goal = own_goal
        self.penalty = penalty


class FoulCommittedEvent(FootballEvent):
    """Input event raised when a referee penalises a side, optionally carding it."""

    def __init__(
        self,
        team: Contestant,
        card: Optional[str] = None,
        offender_id: Optional[str] = None,
        reason: str = "Foul play",
    ) -> None:
        super().__init__()
        self.team = team
        self.card = card
        self.offender_id = offender_id
        self.reason = reason


class EndPeriodEvent(FootballEvent):
    """Input event raised when the referee ends the current period."""

    pass


class PenaltyKickEvent(FootballEvent):
    """Input event raised for a single kick during a penalty shootout."""

    def __init__(self, team: Contestant, scored: bool) -> None:
        super().__init__()
        self.team = team
        self.scored = scored


class GoalScored(FootballEvent):
    def __init__(self, team: Contestant) -> None:
        super().__init__()
        self.team = team


class PlayerCautioned(FootballEvent):
    def __init__(self, team: Contestant, offender_id: str) -> None:
        super().__init__()
        self.team = team
        self.offender_id = offender_id


class PlayerDismissed(FootballEvent):
    def __init__(self, team: Contestant, offender_id: str) -> None:
        super().__init__()
        self.team = team
        self.offender_id = offender_id


class ExtraTimeStarted(FootballEvent):
    pass


class PenaltyShootoutStarted(FootballEvent):
    pass


class MatchEnded(FootballEvent):
    def __init__(
        self,
        winner: Optional[Contestant],
        draw: bool = False,
        decided_by: str = "regulation",
    ) -> None:
        super().__init__()
        self.winner = winner
        self.draw = draw
        self.decided_by = decided_by
