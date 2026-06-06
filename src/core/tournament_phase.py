from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contestant import Contestant

class DrawStrategy(ABC):
    """
    Strategy Pattern: Defines how contestants are matched up for a phase.
    """
    @abstractmethod
    def generate_draw(self, contestants: list[Contestant]) -> list[tuple[Contestant, Contestant]]:
        pass


class TournamentPhase(ABC):
    """
    Base class for a tournament phase (e.g., Group Stage, Knockout).
    Delegates the matching logic to the injected DrawStrategy.
    """
    def __init__(self, name: str, draw_strategy: DrawStrategy) -> None:
        self.name = name
        self.draw_strategy = draw_strategy
        self.is_completed: bool = False

    def get_matchups(self, contestants: list[Contestant]) -> list[tuple[Contestant, Contestant]]:
        """Delegates the bracket generation to the injected strategy."""
        return self.draw_strategy.generate_draw(contestants)


class TournamentPhaseFactory(ABC):
    """
    Factory Pattern: Creates tournament phases dynamically.
    """
    @abstractmethod
    def create_phase(self, phase_name: str) -> TournamentPhase:
        pass