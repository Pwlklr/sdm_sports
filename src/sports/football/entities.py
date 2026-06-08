from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set


class PeriodKind(Enum):
    """Distinguishes the segments of a football match."""

    REGULAR = "Regular"
    EXTRA_TIME = "Extra Time"


class Goal:
    """
    Value Object representing a single goal credited to a side.
    Stores the credited team, optional scorer label, the minute and flags.
    """

    def __init__(
        self,
        team_id: str,
        scorer_id: Optional[str] = None,
        minute: Optional[int] = None,
        own_goal: bool = False,
        penalty: bool = False,
    ) -> None:
        if minute is not None and minute < 0:
            raise ValueError(f"Invalid minute: {minute}. Must be non-negative.")

        self.team_id = team_id
        self.scorer_id = scorer_id
        self.minute = minute
        self.own_goal = own_goal
        self.penalty = penalty

    @property
    def points(self) -> int:
        """Each goal is worth a single point on the scoreline."""
        return 1

    def __str__(self) -> str:
        tags: List[str] = []
        if self.penalty:
            tags.append("pen")
        if self.own_goal:
            tags.append("o.g.")
        suffix = f" ({', '.join(tags)})" if tags else ""
        minute = f"{self.minute}'" if self.minute is not None else "?"
        return f"Goal {minute}{suffix}"


class MatchPeriod:
    """
    Aggregate Root managing the goals scored within a single half.
    Mirrors the role of a turn aggregate: it can be ended exactly once.
    """

    def __init__(
        self, index: int, length_minutes: int, kind: PeriodKind = PeriodKind.REGULAR
    ) -> None:
        self.index = index
        self.length_minutes = length_minutes
        self.kind = kind
        self._goals: List[Goal] = []
        self._ended: bool = False

    def add_goal(self, goal: Goal) -> None:
        """Records a goal in this period if it is still being played."""
        if self._ended:
            raise ValueError("Cannot add a goal. The period is already finished.")
        self._goals.append(goal)

    @property
    def goals(self) -> List[Goal]:
        """Returns a copy of the goals scored in this period."""
        return self._goals.copy()

    @property
    def is_finished(self) -> bool:
        """A period ends when the referee blows the whistle for it."""
        return self._ended

    def end(self) -> None:
        """Flags the period as finished, forcing it to close."""
        self._ended = True


class DisciplinaryRecord:
    """
    Aggregate tracking cautions and dismissals across a match.
    A player accumulating the configured number of yellows is dismissed.
    """

    def __init__(self, yellows_per_dismissal: int = 2) -> None:
        self.yellows_per_dismissal = yellows_per_dismissal
        self.yellow_cards: Dict[str, int] = {}
        self.dismissed: Set[str] = set()

    def caution(self, offender_id: str) -> bool:
        """
        Books a player and returns True when the accumulated yellows
        force a dismissal (e.g. a second caution).
        """
        self.yellow_cards[offender_id] = self.yellow_cards.get(offender_id, 0) + 1
        if self.yellow_cards[offender_id] >= self.yellows_per_dismissal:
            self.dismiss(offender_id)
            return True
        return False

    def dismiss(self, offender_id: str) -> None:
        """Sends a player off; subsequent dismissals are idempotent."""
        self.dismissed.add(offender_id)

    def is_dismissed(self, offender_id: str) -> bool:
        return offender_id in self.dismissed
