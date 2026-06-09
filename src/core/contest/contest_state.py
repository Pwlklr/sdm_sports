from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.contest.event import Event


class ContestState(ABC):
    """
    Stores sport-specific match data. Mutated exclusively through apply(fact).
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

    @abstractmethod
    def apply(self, fact: Event) -> None:
        """Apply a domain fact to this state (bookkeeping only, no rule decisions)."""
        pass
