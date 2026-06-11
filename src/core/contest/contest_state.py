from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.contest.event import Event
from src.core.contest.result import Result
from src.core.contestant.models import Contestant


class ContestState(ABC):
    """
    Event-sourced projection: match data mutated exclusively through apply(fact).
    reset() returns the empty projection used when replaying the event log.
    """

    is_final: bool

    def __init__(self) -> None:
        self.is_final = False

    @property
    def is_completed(self) -> bool:
        return self.is_final

    @is_completed.setter
    def is_completed(self, value: bool) -> None:
        self.is_final = value

    @property
    @abstractmethod
    def contestants(self) -> list[Contestant]:
        """Sides in this match (identity); sport-specific validation in concrete states."""
        pass

    @abstractmethod
    def apply(self, fact: Event) -> None:
        """Apply a domain fact to this projection (bookkeeping only, no rule decisions)."""
        pass

    @abstractmethod
    def reset(self) -> ContestState:
        """Return a fresh projection before any match events (replay entry point)."""
        pass

    @abstractmethod
    def build_result(self) -> Result:
        """Build the sporting outcome from the current projection."""
        pass
