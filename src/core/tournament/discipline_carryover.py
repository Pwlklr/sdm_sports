from __future__ import annotations

from src.core.tournament.sport_tournament_profile import DisciplineCarryover
from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot
from src.core.tournament.tournament_state import DisciplineState


class NullDisciplineCarryover(DisciplineCarryover):
    def carryover(
        self,
        snapshot: MatchOutcomeSnapshot,
        discipline: DisciplineState,
    ) -> list[tuple[str, int]]:
        return []
