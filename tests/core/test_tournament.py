import pytest
from src.core.participants import Team
from src.core.state import ContestState
from src.core.ruleset import RuleSet
from src.core.events import ContestEvent
from src.core.contest import Contest
from src.core.tournament import TournamentPhase, Tournament

class DummyState(ContestState):
    pass

class DummyRuleSet(RuleSet):
    def evaluate(self, event: ContestEvent, state: ContestState) -> None:
        if event.action_type == "END":
            state.is_final = True

class DummyEvent(ContestEvent):
    def __init__(self, action_type: str):
        super().__init__()
        self.action_type = action_type

def test_tournament_phase_observes_contest_completion():
    # Arrange
    team_a = Team("T1", "Team A")
    team_b = Team("T2", "Team B")
    
    contest = Contest("C1", [team_a, team_b], DummyState(), DummyRuleSet())
    phase = TournamentPhase("Phase-1")
    
    # Act: Assign contest to phase (attaches observer)
    phase.add_contest(contest)
    
    # Assert initial state
    assert phase.completed_contests == 0
    
    # Act: Process an event that ends the match
    contest.process_event(DummyEvent("END"))
    
    # Assert: Phase should have been notified that the contest is final
    assert phase.completed_contests == 1