import pytest
from src.core.contestant import IndividualPlayer
from src.sports.darts.state import DartsContestState
from src.sports.darts.entities import DartTurn

def test_state_initialization() -> None:
    p1 = IndividualPlayer("Player 1", "p1")
    p2 = IndividualPlayer("Player 2", "p2")
    
    state = DartsContestState(players=[p1, p2], starting_score=501)
    
    assert state.current_player == p1
    assert state.scores["p1"] == 501
    assert state.scores["p2"] == 501
    assert state.current_turn is None
    assert not state.is_completed

def test_turn_lifecycle_and_player_advancement() -> None:
    p1 = IndividualPlayer("P1", "p1")
    p2 = IndividualPlayer("P2", "p2")
    state = DartsContestState(players=[p1, p2])
    
    # Start turn for P1
    state.start_new_turn()
    assert isinstance(state.current_turn, DartTurn)
    assert state.turn_starting_score == 501
    
    # Advance to P2
    state.advance_player()
    assert state.current_player == p2
    
    # Advance back to P1
    state.advance_player()
    assert state.current_player == p1

def test_leg_reset() -> None:
    p1 = IndividualPlayer("P1", "p1")
    state = DartsContestState(players=[p1])
    
    # Simulate points dropped
    state.scores["p1"] = 100
    state.start_new_turn()
    
    # Reset for next leg
    state.reset_for_new_leg()
    
    assert state.scores["p1"] == 501
    assert state.current_turn is None