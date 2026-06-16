from __future__ import annotations

from src.core.contest.contest_result import ContestResult
from src.core.tournament.default_phase_outcome_interpreter import (
    DefaultPhaseOutcomeInterpreter,
)
from src.core.tournament.discipline_carryover import NullDisciplineCarryover
from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot
from src.core.tournament.sport_tournament_profile import (
    DisciplineCarryover,
    SportTournamentProfile,
)
from src.core.tournament.sport_tournament_registry import SportTournamentRegistry
from src.core.tournament.standings_tiebreaker import DefaultStandingsTiebreaker
from src.core.tournament.tournament_state import DisciplineState
from src.sports.football.contest.football_result import FootballSideMetrics
from src.sports.football.descriptor import FOOTBALL_SPORT

YELLOW_SUSPENSION_THRESHOLD = 2


class FootballPhaseOutcomeInterpreter(DefaultPhaseOutcomeInterpreter):
    def interpret(
        self, contest_id: str, result: ContestResult
    ) -> MatchOutcomeSnapshot:
        snapshot = super().interpret(contest_id, result)
        metrics: dict[str, object] = {}
        side = result.side_metrics()
        if isinstance(side, FootballSideMetrics):
            for player_id, stats in side.all_players().items():
                metrics[player_id] = {
                    "goals": stats.goals,
                    "assists": stats.assists,
                    "yellow_cards": stats.yellow_cards,
                    "dismissed": stats.dismissed,
                }
        return MatchOutcomeSnapshot(
            contest_id=snapshot.contest_id,
            fingerprint=snapshot.fingerprint,
            winner_id=snapshot.winner_id,
            ranking=snapshot.ranking,
            points_deltas=snapshot.points_deltas,
            metrics_blob=metrics or None,
        )


class FootballDisciplineCarryover(DisciplineCarryover):
    def carryover(
        self,
        snapshot: MatchOutcomeSnapshot,
        discipline: DisciplineState,
    ) -> list[tuple[str, int]]:
        if not snapshot.metrics_blob:
            return []
        suspensions: list[tuple[str, int]] = []
        yellow_counts: dict[str, int] = {}
        for player_id, data in snapshot.metrics_blob.items():
            if not isinstance(data, dict):
                continue
            if data.get("dismissed"):
                suspensions.append((player_id, 1))
            yellows = int(data.get("yellow_cards", 0))
            if yellows:
                yellow_counts[player_id] = (
                    discipline.infractions.get(player_id, []).count("yellow")
                    + yellows
                )
        for player_id, total in yellow_counts.items():
            if total >= YELLOW_SUSPENSION_THRESHOLD:
                suspensions.append((player_id, 1))
        return suspensions


def _build_football_tournament_profile() -> SportTournamentProfile:
    return SportTournamentProfile(
        outcome_interpreter=FootballPhaseOutcomeInterpreter(),
        tiebreaker=DefaultStandingsTiebreaker(),
        discipline_carryover=FootballDisciplineCarryover(),
    )


SportTournamentRegistry.register(
    FOOTBALL_SPORT.id, _build_football_tournament_profile
)
