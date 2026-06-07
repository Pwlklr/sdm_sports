from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.core.contest import Contest

class DrawStrategy(ABC):
    """Strategy Pattern: Defines how contestants are matched up."""
    @abstractmethod
    def generate_draw(self, contestants: list[Contestant]) -> list[tuple[Contestant, Contestant]]:
        pass

class TournamentPhase(ABC):
    """Base class for a tournament phase."""
    def __init__(self, name: str, draw_strategy: DrawStrategy) -> None:
        self.name = name
        self.draw_strategy = draw_strategy
        self.is_completed: bool = False
        self.contests: List[Contest] = []

    def get_matchups(self, contestants: list[Contestant]) -> list[tuple[Contestant, Contestant]]:
        return self.draw_strategy.generate_draw(contestants)

    def add_contest(self, contest: Contest) -> None:
        self.contests.append(contest)

    @property
    def completed_contests(self) -> int:
        return len([c for c in self.contests if c.current_state.is_completed])
        
    def check_completion(self) -> None:
        """Evaluates if all contests in this phase are finished."""
        if self.contests and self.completed_contests == len(self.contests):
            self.is_completed = True

class KnockoutPhase(TournamentPhase):
    """A phase where losers are eliminated."""
    pass

class GroupPhase(TournamentPhase):
    """A phase where points are tallied on a leaderboard."""
    pass

class TournamentPhaseFactory(ABC):
    """Factory Pattern: Creates tournament phases dynamically."""
    @abstractmethod
    def create_phase(self, phase_name: str) -> TournamentPhase:
        pass