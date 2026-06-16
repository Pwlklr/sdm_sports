from __future__ import annotations

from src.core.tournament.default_phase_outcome_interpreter import (
    DefaultPhaseOutcomeInterpreter,
)
from src.core.tournament.discipline_carryover import NullDisciplineCarryover
from src.core.tournament.sport_tournament_profile import SportTournamentProfile
from src.core.tournament.sport_tournament_registry import SportTournamentRegistry
from src.core.tournament.sport_tournament_profile import StandingsTiebreaker
from src.core.tournament.phase_state import GroupStandingRow, RoundRobinPhaseState
from src.core.tournament.squad_policy import SquadPolicy
from src.core.tournament.tournament_state import DisciplineState
from src.core.contestant.models import Contestant, IndividualPlayer
from src.core.shared.command_rejected import reject
from src.sports.darts.descriptor import DARTS_SPORT


class DartsStandingsTiebreaker(StandingsTiebreaker):
    """Sorts by points → wins → contestant_id (alphabetical fallback)."""

    def order(self, contestant_ids: list[str], phase_state: object) -> list[str]:
        standings = _extract_standings(phase_state)
        rows: list[GroupStandingRow] = []
        missing: list[str] = []
        for cid in contestant_ids:
            row = standings.get(cid) if standings else None
            if isinstance(row, GroupStandingRow):
                rows.append(row)
            else:
                missing.append(cid)
        rows.sort(
            key=lambda r: (r.points, r.wins, r.contestant_id),
            reverse=True,
        )
        return [r.contestant_id for r in rows] + missing


def _extract_standings(
    phase_state: object,
) -> dict[str, GroupStandingRow] | None:
    if isinstance(phase_state, dict):
        return phase_state
    if isinstance(phase_state, RoundRobinPhaseState):
        return phase_state.standings
    standings = getattr(phase_state, "standings", None)
    if isinstance(standings, dict):
        return standings
    return None


class DartsIndividualSquadPolicy(SquadPolicy):
    def validate_squad(
        self,
        contestant: Contestant,
        player_ids: tuple[str, ...],
    ) -> None:
        if not isinstance(contestant, IndividualPlayer):
            reject("Darts squads are for individual contestants.")
        if player_ids != (contestant.id,):
            reject("Darts tournament squad must be the registered player only.")

    def default_squad(self, contestant: Contestant) -> tuple[str, ...] | None:
        if isinstance(contestant, IndividualPlayer):
            return (contestant.id,)
        return None


def _build_darts_tournament_profile() -> SportTournamentProfile:
    return SportTournamentProfile(
        outcome_interpreter=DefaultPhaseOutcomeInterpreter(),
        tiebreaker=DartsStandingsTiebreaker(),
        squad_policy=DartsIndividualSquadPolicy(),
        discipline_carryover=NullDisciplineCarryover(),
    )


SportTournamentRegistry.register(DARTS_SPORT.id, _build_darts_tournament_profile)
