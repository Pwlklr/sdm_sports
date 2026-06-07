from abc import ABC, abstractmethod
from typing import Optional
from src.core.contestant import Contestant

class Result(ABC):
    """
    Base interface for the outcome of a Match/Contest.
    """
    @abstractmethod
    def is_finished(self) -> bool:
        pass

    @abstractmethod
    def get_winner(self) -> Optional[Contestant]:
        pass