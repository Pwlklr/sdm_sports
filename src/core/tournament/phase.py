from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.core.contest.contest import Contest
    from src.core.contestant.models import Contestant


class DrawStrategy(ABC):
    """Strategy Pattern: Defines how contestants are matched up."""

    @abstractmethod
    def generate_draw(
        self, contestants: list[Contestant]
    ) -> list[tuple[Contestant, Contestant]]:
        pass

    def validate_contestants(self, contestants: list[Contestant]) -> None:
        if len(contestants) < 2:
            raise ValueError("At least two contestants are required for a draw.")


@dataclass
class GroupStanding:
    contestant: Contestant
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points: int = 0


class TournamentPhase(ABC):
    """Base class for a tournament phase with fixture generation and outcome tracking."""

    def __init__(self, name: str, draw_strategy: DrawStrategy) -> None:
        self.name = name
        self.draw_strategy = draw_strategy
        self.is_completed: bool = False
        self.contests: List[Contest] = []

    def get_matchups(
        self, contestants: list[Contestant]
    ) -> list[tuple[Contestant, Contestant]]:
        self.draw_strategy.validate_contestants(contestants)
        return self.draw_strategy.generate_draw(contestants)

    def add_contest(self, contest: Contest) -> None:
        self.contests.append(contest)

    @property
    def completed_contests(self) -> int:
        return len([c for c in self.contests if c.current_state.is_completed])

    def record_match_result(self, contest: Contest) -> None:
        if contest not in self.contests:
            raise ValueError("Contest does not belong to this phase.")
        if not contest.current_state.is_completed:
            raise ValueError("Cannot record result for an incomplete contest.")
        self._apply_result(contest)

    @abstractmethod
    def _apply_result(self, contest: Contest) -> None:
        pass

    def check_completion(self) -> bool:
        if self.contests and self.completed_contests == len(self.contests):
            self.is_completed = True
        return self.is_completed

    @abstractmethod
    def get_qualifiers(self) -> list[Contestant]:
        pass


class KnockoutPhase(TournamentPhase):
    """Elimination phase: winners advance."""

    def __init__(self, name: str, draw_strategy: DrawStrategy) -> None:
        super().__init__(name, draw_strategy)
        self._winners: list[Contestant] = []

    def _apply_result(self, contest: Contest) -> None:
        if contest.result is None:
            return
        winner = contest.result.get_winner()
        if winner is not None and winner not in self._winners:
            self._winners.append(winner)

    def get_qualifiers(self) -> list[Contestant]:
        return self._winners.copy()


class GroupStagePhase(TournamentPhase):
    """Round-robin phase with standings table."""

    def __init__(self, name: str, draw_strategy: DrawStrategy) -> None:
        super().__init__(name, draw_strategy)
        self.standings: dict[str, GroupStanding] = {}

    def initialize_standings(self, contestants: list[Contestant]) -> None:
        for contestant in contestants:
            self.standings[contestant.id] = GroupStanding(contestant=contestant)

    def _apply_result(self, contest: Contest) -> None:
        if contest.result is None:
            return

        sides = contest.contestants
        if len(sides) != 2:
            return

        home, away = sides[0], sides[1]
        if home.id not in self.standings or away.id not in self.standings:
            return

        home_row = self.standings[home.id]
        away_row = self.standings[away.id]
        home_row.played += 1
        away_row.played += 1

        winner = contest.result.get_winner()
        if winner is None:
            home_row.draws += 1
            away_row.draws += 1
            home_row.points += 1
            away_row.points += 1
            return

        if winner.id == home.id:
            home_row.wins += 1
            away_row.losses += 1
            home_row.points += 3
        elif winner.id == away.id:
            away_row.wins += 1
            home_row.losses += 1
            away_row.points += 3

    def get_qualifiers(self) -> list[Contestant]:
        ranked = sorted(
            self.standings.values(),
            key=lambda row: (row.points, row.wins, -row.losses),
            reverse=True,
        )
        if not ranked:
            return []
        return [ranked[0].contestant]


GroupPhase = GroupStagePhase


class TournamentPhaseFactory(ABC):
    """Factory Pattern: Creates tournament phases dynamically."""

    @abstractmethod
    def create_phase(self, phase_name: str) -> TournamentPhase:
        pass
