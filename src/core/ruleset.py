from abc import ABC, abstractmethod
from src.core.events import ContestEvent
from src.core.state import ContestState

class RuleSet(ABC):
    """
    Validates in-match events based on the business rules specific to a given sport 
    and tournament phase.
    """
    @abstractmethod
    def evaluate(self, event: ContestEvent, state: ContestState) -> None:
        pass