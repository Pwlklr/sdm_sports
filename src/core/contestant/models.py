import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class Contestant(ABC):
    """
    Base interface for any entity participating in a match (Individual or Team).
    """

    def __init__(
        self,
        name: str,
        contestant_id: str | None = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.id = contestant_id or str(uuid.uuid4())
        self.metadata: Dict[str, str] = metadata or {}

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Returns the formatted name of the contestant."""
        pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contestant):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class IndividualPlayer(Contestant):
    """
    Represents a single physical player (e.g., a Darts player).
    """

    @property
    def display_name(self) -> str:
        return self.name


class Team(Contestant):
    """
    Represents a collection of players (e.g., a Football team or Darts doubles team).
    """

    def __init__(
        self,
        name: str,
        contestant_id: str | None = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(name, contestant_id, metadata)
        self._roster: List[IndividualPlayer] = []

    def add_player(self, player: IndividualPlayer) -> None:
        """Adds a player to the team roster if not already present."""
        if player not in self._roster:
            self._roster.append(player)

    def remove_player(self, player: IndividualPlayer) -> None:
        """Removes a player from the team roster."""
        if player in self._roster:
            self._roster.remove(player)

    @property
    def roster(self) -> List[IndividualPlayer]:
        """Returns a copy of the current roster."""
        return self._roster.copy()

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        return f"{self.name} ({len(self._roster)} players)"
