import pytest
from src.core.contest import Contest
from src.core.contestant import IndividualPlayer
from src.core.contest_state import ContestState
from src.core.ruleset import RuleSet
from src.core.contest_event import ContestEvent

class MockState(ContestState):
    pass

class MockEvent(ContestEvent):
    pass

def dummy_handler(event: ContestEvent, state: ContestState) -> None:
    pass

class MockRuleSet(RuleSet):
    # Satisfy the strict __init_subclass__ requirement of the existing RuleSet
    handlers = {MockEvent: dummy_handler}
    
    def evaluate(self, event: ContestEvent, state: ContestState) -> None:
        pass

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