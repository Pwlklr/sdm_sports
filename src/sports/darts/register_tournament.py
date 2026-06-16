from __future__ import annotations

from src.core.tournament.default_phase_outcome_interpreter import (
    DefaultPhaseOutcomeInterpreter,
)
from src.core.tournament.discipline_carryover import NullDisciplineCarryover
from src.core.tournament.sport_tournament_profile import SportTournamentProfile
from src.core.tournament.sport_tournament_registry import SportTournamentRegistry
from src.core.tournament.standings_tiebreaker import DefaultStandingsTiebreaker
from src.sports.darts.descriptor import DARTS_SPORT


def _build_darts_tournament_profile() -> SportTournamentProfile:
    return SportTournamentProfile(
        outcome_interpreter=DefaultPhaseOutcomeInterpreter(),
        tiebreaker=DefaultStandingsTiebreaker(),
        discipline_carryover=NullDisciplineCarryover(),
    )


SportTournamentRegistry.register(DARTS_SPORT.id, _build_darts_tournament_profile)
