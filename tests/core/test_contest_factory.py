from __future__ import annotations

from dataclasses import dataclass

from src.core.contest import Contest, ContestFactory
from src.core.contest.command import Command
from src.core.contest.contest_factory import ContestAssembly
from src.core.contest.event import Event
from src.core.contestant import IndividualPlayer
from src.core.contest.rule_set import RuleSet
from tests.core.contest_test_support import (
    StubResultBuilder,
    StatefulContestState,
    make_contest,
)


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


def _register_mock_builder() -> None:
    def build(
        contestants: list, _config: object, **_: object
    ) -> ContestAssembly:
        return ContestAssembly(
            state=MockState(contestants),
            ruleset=MockRuleSet(),
            result_builder=StubResultBuilder(),
        )

    if "mock" not in ContestFactory._builders:
        ContestFactory.register("mock", build)


def test_contest_factory_creates_contest_for_registered_sport() -> None:
    _register_mock_builder()
    p1 = IndividualPlayer("Player 1")
    contest = ContestFactory.create("mock", [p1], object())

    assert isinstance(contest.current_state, MockState)
    assert contest.contestants == [p1]
    assert contest.id is not None


def test_make_contest_helper_builds_contest_directly() -> None:
    p1 = IndividualPlayer("Player 1")
    contest = make_contest(MockState([p1]), MockRuleSet())
    assert len(contest.contestants) == 1
    assert isinstance(contest, Contest)
