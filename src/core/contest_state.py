from __future__ import annotations
from abc import ABC

class ContestState(ABC):
    """
    A structure storing the current, sport-specific state of an ongoing match.
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