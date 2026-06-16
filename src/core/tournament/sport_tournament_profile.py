from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.tournament.phase_outcome_interpreter import PhaseOutcomeInterpreter
from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot
from src.core.tournament.tournament_state import DisciplineState


class StandingsTiebreaker(ABC):
    @abstractmethod
    def order(self, contestant_ids: list[str], standings: object) -> list[str]:
        pass


class DisciplineCarryover(ABC):
    @abstractmethod
    def carryover(
        self,
        snapshot: MatchOutcomeSnapshot,
        discipline: DisciplineState,
    ) -> list[tuple[str, int]]:
        """Return list of (player_id, suspension_matches)."""


@dataclass(frozen=True, kw_only=True)
class SportTournamentProfile:
    outcome_interpreter: PhaseOutcomeInterpreter
    tiebreaker: StandingsTiebreaker
    discipline_carryover: DisciplineCarryover | None = None
