from abc import ABC, abstractmethod
from typing import Optional
from src.core.contest import Contest
from src.core.contestant import Contestant
from src.core.commands import MatchCommand

class SportPlugin(ABC):
    """Contract for plugging a new sports discipline into the generic SDM system."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def interactive_setup(self) -> Contest:
        pass

    @abstractmethod
    def create_match(self, players: list[Contestant]) -> Contest:
        """Called by the Tournament Engine to generate a configured match."""
        pass

    @abstractmethod
    def parse_command(self, user_input: str, contest: Contest) -> Optional[MatchCommand]:
        pass