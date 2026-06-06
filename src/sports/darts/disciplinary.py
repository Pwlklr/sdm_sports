from __future__ import annotations
from typing import TYPE_CHECKING
from src.core.disciplinary import Violation, Penalty

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.sports.darts.entities import DartTurn

class OcheFaultViolation(Violation):
    """Detects if a player stepped over the line."""
    def __init__(self, violator: Contestant) -> None:
        super().__init__(violator, "Stepped over the oche line")

class InvalidThrowPenalty(Penalty):
    """Invalidates a dart (scores 0), but counts towards the 3-dart limit."""
    def apply(self, state: DartTurn) -> None:
        # Note: The logic for setting the throw to 0 is handled 
        # when the RuleSet evaluates this penalty against a specific throw.
        pass

class BustViolation(Violation):
    """Detects if a turn's score exceeds remaining points or hits an illegal double."""
    def __init__(self, violator: Contestant, reason: str) -> None:
        super().__init__(violator, reason)

class BustPenalty(Penalty):
    """Voids the score of the current turn and forces it to end."""
    def apply(self, state: DartTurn) -> None:
        state.mark_busted()