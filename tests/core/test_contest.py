import pytest
from src.core.state import ContestState
from src.core.ruleset import RuleSet
from src.core.events import ContestEvent
from src.core.contest import Contest
from src.core.participants import Team

class DummyState(ContestState):
    def __init__(self):
        super().__init__()
        self.score = 0

class DummyRuleSet(RuleSet):
    def evaluate(self, event: ContestEvent, state: ContestState) -> None:
        if event.team_id == "T1":
            state.score += 1

class DummyEvent(ContestEvent):
    pass

def test_contest_event_delegation():
    # Arrange
    team = Team(team_id="T1", name="Test Team")
    initial_state = DummyState()
    ruleset = DummyRuleSet()
    
    contest = Contest(
        contest_id="C1",
        teams=[team],
        initial_state=initial_state,
        ruleset=ruleset
    )

    # Act
    event = DummyEvent(team_id="T1")
    contest.process_event(event)

    # Assert
    assert contest.current_state.score == 1