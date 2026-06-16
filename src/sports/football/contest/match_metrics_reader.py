from __future__ import annotations

from src.core.contest.contest_result import ContestResult
from src.core.contest.match_metrics_reader import MatchMetricsReader
from src.sports.football.contest.football_result import FootballSideMetrics


class FootballMatchMetricsReader(MatchMetricsReader):
    """Reads player stats nested in side_metrics for presentation."""

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
