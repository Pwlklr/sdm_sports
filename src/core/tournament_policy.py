from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.tournament_event import TournamentEvent
    from src.core.tournament_state import TournamentState


class TournamentPolicy(ABC):
    """
    Defines and enforces the global business rules of the entire tournament
    by reacting to lifecycle events.
    """
    @abstractmethod
    def handle(
        self,
        event: TournamentEvent,
        state: TournamentState,
    ) -> list[TournamentEvent]:
        pass
