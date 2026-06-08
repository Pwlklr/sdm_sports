import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    # Forward declaration to avoid circular imports. 
    # Will be strictly typed to ContestState once that module is refined.
    from src.core.contest_state import ContestState


class Violation(ABC):
    """
    Represents a rule breach committed by a Contestant during a match.
    (e.g., BustViolation, OcheFaultViolation, FoulViolation)
    """
    def __init__(self, violator: 'Contestant', reason: str, violation_id: str | None = None) -> None:
        self.violator = violator
        self.reason = reason
        self.id = violation_id or str(uuid.uuid4())

    def __str__(self) -> str:
        return f"Violation by {self.violator.display_name}: {self.reason}"


# TODO: Zmienic na contestantstate
class Penalty(ABC):
    """
    Enforces the consequences of a Violation by mutating the ContestState.
    (e.g., BustPenalty, InvalidThrowPenalty, YellowCardPenalty)
    """
    def __init__(self, violation: Violation, penalty_id: str | None = None) -> None:
        self.violation = violation
        self.id = penalty_id or str(uuid.uuid4())

    @abstractmethod
    def apply(self, state: Any) -> None:
        """
        Applies the penalty to the given contest state.
        Type hint is Any here temporarily to avoid circular imports 
        until ContestState is finalized, but will act on ContestState.
        """
        pass