from __future__ import annotations

from src.core.contest.contest_result import ContestResult
from src.core.contest.match_metrics_reader import MatchMetricsReader
from src.sports.darts.contest.darts_result import DartsSideMetrics


class DartsMatchMetricsReader(MatchMetricsReader):
    """Reads side_metrics from darts ContestResult (player equals side)."""

    def player_totals(self, result: ContestResult) -> DartsSideMetrics:
        side = result.side_metrics()
        if not isinstance(side, DartsSideMetrics):
            raise TypeError("Expected DartsSideMetrics.")
        return side
