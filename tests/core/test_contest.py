from __future__ import annotations

import pytest

from dataclasses import dataclass

from src.core.contest.command import Command
from tests.core.contest_test_support import StatefulContestState, make_contest
from src.core.contest.event import Event
from src.core.contestant import IndividualPlayer
from src.core.contest.rule_set import RuleSet


@dataclass(frozen=True, kw_only=True)
class MockCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class MockFact(Event):
    pass


class MockState(StatefulContestState):
    def apply(self, fact: Event) -> MockState:
        return MockState(self.contestants)

    def reset(self) -> MockState:
        return MockState(self.contestants)


class MockRuleSet(RuleSet):
    def decide_mock(self, command: MockCommand, state: MockState) -> list[Event]:
        return [MockFact()]

    command_handlers = {MockCommand: decide_mock}
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
    assert contest.result.played is None
    assert not contest.result.is_finished()


def test_get_final_result_raises_when_match_not_completed() -> None:
    contest = make_contest(MockState([]), MockRuleSet())
    with pytest.raises(ValueError, match="not completed"):
        contest.get_final_result()


def test_contest_handle_emits_facts() -> None:
    p1 = IndividualPlayer("Player 1")
    state = MockState([p1])
    ruleset = MockRuleSet()
    contest = make_contest(state, ruleset)

    emitted = contest.handle(MockCommand())

    assert len(emitted) == 1
    assert isinstance(emitted[0], MockFact)
    assert len(contest.history) == 1
