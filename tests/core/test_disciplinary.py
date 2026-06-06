import pytest
from src.core.contestant import IndividualPlayer
from src.core.disciplinary import Violation, Penalty

class MockState:
    """A dummy state to test penalty application."""
    def __init__(self) -> None:
        self.penalty_points = 0

class MockViolation(Violation):
    """A concrete dummy violation."""
    pass

class MockPenalty(Penalty):
    """A concrete dummy penalty that adds 10 penalty points to the state."""
    def apply(self, state: MockState) -> None:
        state.penalty_points += 10

def test_violation_creation() -> None:
    violator = IndividualPlayer("Bad Player")
    violation = MockViolation(violator=violator, reason="Stepped over the line")
    
    assert violation.violator == violator
    assert violation.reason == "Stepped over the line"
    assert violation.id is not None
    assert str(violation) == "Violation by Bad Player: Stepped over the line"

def test_penalty_application() -> None:
    violator = IndividualPlayer("Bad Player")
    violation = MockViolation(violator=violator, reason="Foul")
    penalty = MockPenalty(violation=violation)
    
    state = MockState()
    assert state.penalty_points == 0
    
    # The penalty acts on the state (Strategy/Visitor pattern concept)
    penalty.apply(state)
    assert state.penalty_points == 10
    assert penalty.violation == violation