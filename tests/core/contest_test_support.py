from __future__ import annotations

from dataclasses import dataclass

from src.core.contest import Contest
from src.core.contest.contest_result import ContestResult, EmptySideMetrics, RankedEntry
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event
from src.core.contest.metrics import SideMetrics
from src.core.contest.result_builder import ResultBuilder
from src.core.contest.rule_set import RuleSet
from src.core.contestant.models import Contestant


@dataclass(frozen=True, kw_only=True)
class EmptyContestResult(ContestResult):
    def is_finished(self) -> bool:
        return False

    def ranking(self) -> tuple[RankedEntry, ...]:
        return ()

    def side_metrics(self) -> SideMetrics:
        return EmptySideMetrics()


EmptyResult = EmptyContestResult


class StubResultBuilder:
    def build(self, state: ContestState) -> ContestResult:
        return EmptyContestResult()


class StatefulContestState:
    def __init__(self, contestants: list[Contestant] | None = None) -> None:
        self._contestants = list(contestants or [])
        self._finished = False

    @property
    def is_finished(self) -> bool:
        return self._finished

    @property
    def contestants(self) -> list[Contestant]:
        return list(self._contestants)

    def apply(self, fact: Event) -> StatefulContestState:
        return self

    def reset(self) -> StatefulContestState:
        return StatefulContestState(self.contestants)


class MinimalContestState(StatefulContestState):
    def apply(self, fact: Event) -> MinimalContestState:
        return MinimalContestState(self.contestants)

    def reset(self) -> MinimalContestState:
        return MinimalContestState(self.contestants)


def make_contest(
    state: ContestState,
    ruleset: RuleSet,
    *,
    result_builder: ResultBuilder | None = None,
    contest_id: str | None = None,
) -> Contest:
    return Contest(
        state,
        ruleset,
        result_builder or StubResultBuilder(),
        contest_id=contest_id,
    )
