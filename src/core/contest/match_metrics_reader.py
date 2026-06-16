from __future__ import annotations


from typing import Protocol


class MatchMetricsReader(Protocol):
    """Extracts match metrics from ContestResult.side_metrics() for tournament aggregation."""
