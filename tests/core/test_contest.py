from dataclasses import dataclass

from src.core.contest.command import Command
from src.core.contest import Contest
from src.core.contest.event import Event
from src.core.contestant import IndividualPlayer
from src.core.contest.contest_state import ContestState
from src.core.contest.rule_set import RuleSet


@dataclass(frozen=True, kw_only=True)
class MockCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class MockFact(Event):
    pass


class MockState(ContestState):
    def apply(self, fact: Event) -> None:
        pass


class MockRuleSet(RuleSet):
    def decide_mock(self, command: MockCommand, state: MockState) -> list[Event]:
        return [MockFact()]

    command_handlers = {MockCommand: decide_mock}
    reaction_handlers = {}


def test_contest_initialization() -> None:
    p1 = IndividualPlayer("Player 1")
    p2 = IndividualPlayer("Player 2")
    state = MockState()
    ruleset = MockRuleSet()

    contest = Contest(contestants=[p1, p2], initial_state=state, ruleset=ruleset)

    assert contest.id is not None
    assert len(contest.contestants) == 2
    assert contest.current_state == state
    assert contest.result is None


def test_contest_handle_emits_facts() -> None:
    p1 = IndividualPlayer("Player 1")
    state = MockState()
    ruleset = MockRuleSet()
    contest = Contest(contestants=[p1], initial_state=state, ruleset=ruleset)

    emitted = contest.handle(MockCommand())

    assert len(emitted) == 1
    assert isinstance(emitted[0], MockFact)
    assert len(contest.history) == 1
