import pytest
from src.core.contestant import IndividualPlayer
from src.core.disciplinary import Penalty
from src.sports.darts.entities import DartTurn, DartThrow
from src.sports.darts.disciplinary import (
    OcheFaultViolation, InvalidThrowPenalty, 
    BustViolation, BustPenalty
)

def test_oche_fault_pipeline() -> None:
    player = IndividualPlayer("Player 1")
    violation = OcheFaultViolation(player)
    penalty = InvalidThrowPenalty(violation)
    
    assert violation.violator == player
    assert isinstance(penalty, Penalty)

def test_bust_pipeline() -> None:
    player = IndividualPlayer("Player 1")
    turn = DartTurn()
    turn.add_throw(DartThrow(20, 3)) # 60 points
    
    violation = BustViolation(player, "Bust!")
    penalty = BustPenalty(violation)
    
    # Verify penalty forces the turn to end
    penalty.apply(turn)
    assert turn.is_finished
    assert turn.is_busted