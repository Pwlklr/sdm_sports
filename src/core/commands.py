from abc import ABC, abstractmethod
from src.core.contest import Contest

class MatchCommand(ABC):
    """
    Command Pattern: Encapsulates a user action or system trigger 
    to be executed against a specific match.
    """
    @abstractmethod
    def execute(self, match: Contest) -> None:
        pass