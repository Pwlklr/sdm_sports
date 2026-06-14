from __future__ import annotations

from src.core.contest.contest_result import ContestResult
from src.core.tournament.tournament_disciplinary_board import TournamentDisciplinaryBoard
from src.sports.football.contest.football_result import FootballSideMetrics

YELLOW_SUSPENSION_THRESHOLD = 2


class FootballMatchMetricsReader:
    """Reads player stats nested in side_metrics for tournament aggregation."""

    def accrue_disciplinary(
        self,
        result: ContestResult,
        board: TournamentDisciplinaryBoard,
        *,
        yellow_threshold: int = YELLOW_SUSPENSION_THRESHOLD,
    ) -> None:
        side = result.side_metrics()
        if not isinstance(side, FootballSideMetrics):
            return
        for player_id, stats in side.all_players().items():
            if stats.dismissed:
                board.suspend(player_id, 1)
            for _ in range(stats.yellow_cards):
                board.log_infraction_id(player_id, "yellow")
            total = board.infraction_count(player_id, "yellow")
            if total >= yellow_threshold:
                board.suspend(player_id, 1)
                board.log_infraction_id(player_id, "yellow_suspension_served")
                for _ in range(total):
                    board.records[player_id].remove("yellow")

    def top_scorers(self, result: ContestResult) -> list[tuple[str, int]]:
        side = result.side_metrics()
        if not isinstance(side, FootballSideMetrics):
            return []
        scorers = [
            (player_id, stats.goals)
            for player_id, stats in side.all_players().items()
            if stats.goals > 0
        ]
        scorers.sort(key=lambda item: (-item[1], item[0]))
        return scorers
