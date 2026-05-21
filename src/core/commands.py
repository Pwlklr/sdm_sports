from abc import ABC, abstractmethod
from src.core.contest import Contest

class MatchCommand(ABC):
    @abstractmethod
    def execute(self, contest: Contest) -> None:
        pass