from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot
from src.core.tournament.phase_outcome_interpreter import PhaseOutcomeInterpreter
from src.core.tournament.squad_policy import SquadPolicy
from src.core.tournament.tournament_state import DisciplineState


class StandingsTiebreaker(ABC):
    @abstractmethod
    def order(self, contestant_ids: list[str], phase_state: object) -> list[str]:
        """Return contestant_ids sorted by tiebreaker criteria (best first).

        ``phase_state`` is a ``PhaseState`` instance; typed as ``object`` here
        to avoid a circular import at the ABC level.
        """


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
    squad_policy: SquadPolicy
    discipline_carryover: DisciplineCarryover | None = None
