from __future__ import annotations



from src.core.contest import Contest

from src.core.contest.contest_state import ContestState

from src.core.contest.event import Event

from src.core.contest.result import Result

from src.core.contest.rule_set import RuleSet

from src.core.contestant.models import Contestant





class EmptyResult(Result):

    def is_finished(self) -> bool:

        return False





class StatefulContestState(ContestState):

    """Test/prototype projection that holds match contestants."""



    def __init__(self, contestants: list[Contestant] | None = None) -> None:

        super().__init__()

        self._contestants = list(contestants or [])



    @property

    def contestants(self) -> list[Contestant]:

        return list(self._contestants)





class MinimalContestState(StatefulContestState):

    """Test projection with event-sourcing hooks."""



    def apply(self, fact: Event) -> None:

        pass



    def reset(self) -> MinimalContestState:

        return MinimalContestState(self.contestants)



    def build_result(self) -> Result:

        return EmptyResult()





def make_contest(

    state: ContestState,

    ruleset: RuleSet,

    *,

    contest_id: str | None = None,

) -> Contest:

    return Contest(state, ruleset, contest_id=contest_id)

