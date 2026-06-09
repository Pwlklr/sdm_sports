from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set


class PeriodKind(Enum):
    REGULAR = "Regular"
    EXTRA_TIME = "Extra Time"


class Goal:
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
        return 1


class MatchPeriod:
    """Read model: goals recorded within a single half."""

    def __init__(
        self, index: int, length_minutes: int, kind: PeriodKind = PeriodKind.REGULAR
    ) -> None:
        self.index = index
        self.length_minutes = length_minutes
        self.kind = kind
        self._goals: List[Goal] = []
        self._ended: bool = False

    def add_goal(self, goal: Goal) -> None:
        self._goals.append(goal)

    @property
    def goals(self) -> List[Goal]:
        return self._goals.copy()

    @property
    def is_finished(self) -> bool:
        return self._ended

    def end(self) -> None:
        self._ended = True


class DisciplinaryRecord:
    """Read model: card counts and dismissals."""

    def __init__(self) -> None:
        self.yellow_cards: Dict[str, int] = {}
        self.dismissed: Set[str] = set()

    def record_yellow(self, offender_id: str) -> None:
        self.yellow_cards[offender_id] = self.yellow_cards.get(offender_id, 0) + 1

    def dismiss(self, offender_id: str) -> None:
        self.dismissed.add(offender_id)

    def yellows_for(self, offender_id: str) -> int:
        return self.yellow_cards.get(offender_id, 0)

    def is_dismissed(self, offender_id: str) -> bool:
        return offender_id in self.dismissed
