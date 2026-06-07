from abc import ABC, abstractmethod
from typing import Optional, List, Any
from src.core.contest import Contest
from src.core.contestant import Contestant
from src.core.commands import MatchCommand

class SportPlugin(ABC):
    """
    Abstract base class for sport-specific logic. 
    Allows the central engine to handle any sport polymorphically.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of the sport (e.g., 'Professional Darts')."""
        pass

    @abstractmethod
    def setup_exhibition_match(self, selected_players: List[Contestant]) -> Optional[Contest]:
        """Interactive prompt to set up a single match. Returns the configured Contest."""
        pass

    @abstractmethod
    def setup_tournament_config(self) -> Any:
        """Interactive prompt to get tournament rules. Returns a custom config object."""
        pass

    @abstractmethod
    def create_tournament_match(self, match_players: List[Contestant], config: Any) -> Contest:
        """Instantiates a match using the pre-defined tournament config."""
        pass

    @abstractmethod
    def get_start_command(self) -> Optional[MatchCommand]:
        """Provides the specific command needed to trigger the match start lifecycle."""
        pass

    @abstractmethod
    def get_input_prompt(self, contest: Contest) -> str:
        """Provides a sport-specific hint for the command line input."""
        pass

    @abstractmethod
    def parse_command(self, user_input: str, contest: Contest) -> Optional[MatchCommand]:
        """Parses raw string input into a domain-specific MatchCommand."""
        pass