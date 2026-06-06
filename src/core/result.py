from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.contestant import Contestant

class Result(ABC):
    """
    Generic contract for the outcome of a match.
    """
    @abstractmethod
    def is_finished(self) -> bool:
        pass

    @abstractmethod
    def get_winner(self) -> Optional['Contestant']:
        pass