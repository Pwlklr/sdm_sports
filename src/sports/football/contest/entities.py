from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Optional


class PeriodKind(Enum):
    REGULAR = "Regular"
    EXTRA_TIME = "Extra Time"


@dataclass(frozen=True, kw_only=True)
class Goal:
    team_id: str
    scorer_id: Optional[str] = None
    minute: Optional[int] = None
    own_goal: bool = False
    penalty: bool = False

    def __post_init__(self) -> None:
        if self.minute is not None and self.minute < 0:
            raise ValueError(f"Invalid minute: {self.minute}. Must be non-negative.")

    @property
    def points(self) -> int:
        return 1


@dataclass(frozen=True, kw_only=True)
class MatchPeriod:
    index: int
    length_minutes: int
    kind: PeriodKind = PeriodKind.REGULAR
    goals: tuple[Goal, ...] = ()
    ended: bool = False

    def with_goal(self, goal: Goal) -> MatchPeriod:
        return replace(self, goals=self.goals + (goal,))

    def with_ended(self) -> MatchPeriod:
        return replace(self, ended=True)

    @property
    def is_finished(self) -> bool:
        return self.ended


@dataclass(frozen=True, kw_only=True)
class MatchLineup:
    starting: frozenset[str]
    bench: frozenset[str]
    subs_made: int = 0

    def is_on_pitch(self, player_id: str) -> bool:
        return player_id in self.starting

    def is_on_bench(self, player_id: str) -> bool:
        return player_id in self.bench

    def with_substitution(self, player_out: str, player_in: str) -> MatchLineup:
        starting = set(self.starting)
        bench = set(self.bench)
        starting.discard(player_out)
        starting.add(player_in)
        bench.discard(player_in)
        bench.add(player_out)
        return replace(
            self,
            starting=frozenset(starting),
            bench=frozenset(bench),
            subs_made=self.subs_made + 1,
        )

    def active_on_pitch(self, dismissed: frozenset[str]) -> int:
        return sum(1 for player_id in self.starting if player_id not in dismissed)


@dataclass(frozen=True, kw_only=True)
class DisciplinaryRecord:
    yellow_cards: dict[str, int] = field(default_factory=dict)
    dismissed: frozenset[str] = frozenset()

    def with_yellow(self, offender_id: str) -> DisciplinaryRecord:
        cards = dict(self.yellow_cards)
        cards[offender_id] = cards.get(offender_id, 0) + 1
        return replace(self, yellow_cards=cards)

    def with_dismissal(self, offender_id: str) -> DisciplinaryRecord:
        return replace(self, dismissed=self.dismissed | {offender_id})

    def yellows_for(self, offender_id: str) -> int:
        return self.yellow_cards.get(offender_id, 0)

    def is_dismissed(self, offender_id: str) -> bool:
        return offender_id in self.dismissed
