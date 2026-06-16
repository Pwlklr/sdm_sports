from __future__ import annotations

from src.core.contest.contest_result import ContestResult
from src.core.tournament.default_phase_outcome_interpreter import (
    DefaultPhaseOutcomeInterpreter,
)
from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot
from src.core.tournament.sport_tournament_profile import (
    DisciplineCarryover,
    SportTournamentProfile,
)
from src.core.tournament.sport_tournament_registry import SportTournamentRegistry
from src.core.tournament.sport_tournament_profile import StandingsTiebreaker
from src.core.tournament.phase_state import GroupStandingRow, RoundRobinPhaseState
from src.core.tournament.tournament_state import DisciplineState
from src.sports.football.contest.football_result import FootballSideMetrics
from src.core.contestant.models import Contestant, Team
from src.core.shared.command_rejected import reject
from src.core.tournament.squad_policy import SquadPolicy
from src.sports.football.descriptor import FOOTBALL_SPORT

YELLOW_SUSPENSION_THRESHOLD = 2


class FootballPhaseOutcomeInterpreter(DefaultPhaseOutcomeInterpreter):
    def interpret(self, contest_id: str, result: ContestResult) -> MatchOutcomeSnapshot:
        snapshot = super().interpret(contest_id, result)
        metrics: dict[str, object] = {}
        side = result.side_metrics()
        if isinstance(side, FootballSideMetrics):
            for player_id, stats in side.all_players().items():
                metrics[player_id] = {
                    "goals": stats.goals,
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
                    discipline.infractions.get(player_id, []).count("yellow") + yellows
                )
        for player_id, total in yellow_counts.items():
            if total >= YELLOW_SUSPENSION_THRESHOLD:
                suspensions.append((player_id, 1))
        return suspensions


class FootballSquadPolicy(SquadPolicy):
    min_squad_size: int = 14
    max_squad_size: int = 23

    def validate_squad(
        self,
        contestant: Contestant,
        player_ids: tuple[str, ...],
    ) -> None:
        if not isinstance(contestant, Team):
            reject("Football squads require a Team contestant.")
        if len(player_ids) < self.min_squad_size:
            reject(f"Squad must have at least {self.min_squad_size} players.")
        if len(player_ids) > self.max_squad_size:
            reject(f"Squad must have at most {self.max_squad_size} players.")
        if len(set(player_ids)) != len(player_ids):
            reject("Duplicate players in squad.")


class FootballStandingsTiebreaker(StandingsTiebreaker):
    """Sorts by points → wins → contestant_id (alphabetical fallback).

    Goal difference tiebreaking requires per-match goal data to be accumulated
    into the tournament standings, which is not yet wired. For now the ordering
    is: points, wins, then contestant_id for a stable sort.
    """

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


def _build_football_tournament_profile() -> SportTournamentProfile:
    return SportTournamentProfile(
        outcome_interpreter=FootballPhaseOutcomeInterpreter(),
        tiebreaker=FootballStandingsTiebreaker(),
        squad_policy=FootballSquadPolicy(),
        discipline_carryover=FootballDisciplineCarryover(),
    )


SportTournamentRegistry.register(FOOTBALL_SPORT.id, _build_football_tournament_profile)
