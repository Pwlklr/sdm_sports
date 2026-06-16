from __future__ import annotations



from dataclasses import dataclass



from src.core.contest import Contest

from src.core.contest.command import Command

from src.core.contest.contest_result import ContestResult, RankedEntry

from src.core.contest.contest_state import ContestState

from src.core.contest.event import Event, OfficialOverrideEvent

from src.core.contest.metrics import SideMetrics

from src.core.contest.result_builder import ResultBuilder

from src.core.contest.rule_set import RuleSet

from src.core.contestant.models import Contestant





@dataclass(frozen=True, kw_only=True)

class EmptySideMetrics:

    """Minimal side metrics for test stubs."""





@dataclass(frozen=True, kw_only=True)

class EmptyContestResult(ContestResult):

    def is_finished(self) -> bool:

        return False



    def ranking(self) -> tuple[RankedEntry, ...]:

        return ()



    def side_metrics(self) -> SideMetrics:

        return EmptySideMetrics()





EmptyResult = EmptyContestResult





@dataclass(frozen=True, kw_only=True)

class MockOfficialOverride(OfficialOverrideEvent):

    reason: str = "test_override"





class StubResultBuilder(ResultBuilder):

    def build(self, state: ContestState) -> ContestResult:

        return EmptyContestResult()



    def build_official(

        self, state: ContestState, override: OfficialOverrideEvent

    ) -> ContestResult:

        return self.build(state)





class StatefulContestState(ContestState):

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


