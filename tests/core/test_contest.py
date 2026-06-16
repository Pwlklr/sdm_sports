from __future__ import annotations



import pytest



from dataclasses import dataclass



from src.core.contest.command import Command

from tests.core.contest_test_support import (

    MockOfficialOverride,

    StatefulContestState,

    make_contest,

)

from src.core.contest.event import Event, OfficialOverrideEvent, ProjectionEvent

from src.core.contestant import IndividualPlayer

from src.core.contest.rule_set import RuleSet





@dataclass(frozen=True, kw_only=True)

class MockCommand(Command):

    pass





@dataclass(frozen=True, kw_only=True)

class EndCommand(Command):

    pass





@dataclass(frozen=True, kw_only=True)

class MockFact(ProjectionEvent):

    pass





@dataclass(frozen=True, kw_only=True)

class EndFact(ProjectionEvent):

    pass





@dataclass(frozen=True, kw_only=True)

class OverrideCommand(Command):

    pass





class MockState(StatefulContestState):

    def apply(self, fact: Event) -> MockState:

        if isinstance(fact, EndFact):

            finished = MockState(self.contestants)

            finished._finished = True

            return finished

        return MockState(self.contestants)



    def reset(self) -> MockState:

        return MockState(self.contestants)





class MockRuleSet(RuleSet):

    def decide_mock(

        self, command: MockCommand, state: MockState, history: list[Event]

    ) -> list[Event]:

        return [MockFact()]



    def decide_end(

        self, command: EndCommand, state: MockState, history: list[Event]

    ) -> list[Event]:

        return [EndFact()]



    def decide_override(

        self, command: OverrideCommand, state: MockState, history: list[Event]

    ) -> list[Event]:

        return [MockOfficialOverride(reason="admin")]



    command_handlers = {

        MockCommand: decide_mock,

        EndCommand: decide_end,

        OverrideCommand: decide_override,

    }

    reaction_handlers = {}





def test_contest_initialization() -> None:

    p1 = IndividualPlayer("Player 1")

    p2 = IndividualPlayer("Player 2")

    state = MockState([p1, p2])

    ruleset = MockRuleSet()



    contest = make_contest(state, ruleset)



    assert contest.id is not None

    assert len(contest.contestants) == 2

    assert contest.current_state.contestants == state.contestants





def test_get_official_result_raises_when_match_not_completed() -> None:

    contest = make_contest(MockState([]), MockRuleSet())

    with pytest.raises(ValueError, match="not completed"):

        contest.get_official_result()





def test_contest_handle_emits_facts() -> None:

    p1 = IndividualPlayer("Player 1")

    state = MockState([p1])

    ruleset = MockRuleSet()

    contest = make_contest(state, ruleset)



    emitted = contest.handle(MockCommand())



    assert len(emitted) == 1

    assert isinstance(emitted[0], MockFact)

    assert len(contest.history) == 1





def test_official_override_event_does_not_mutate_state() -> None:

    state = MockState([])

    ruleset = MockRuleSet()

    contest = make_contest(state, ruleset)



    contest.handle(OverrideCommand())



    assert len(contest.history) == 1

    assert isinstance(contest.history[0], OfficialOverrideEvent)


