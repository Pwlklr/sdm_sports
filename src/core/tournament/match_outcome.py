from __future__ import annotations

from dataclasses import dataclass

from src.core.contestant.models import Contestant


@dataclass(frozen=True)
class HeadToHeadPoints:
    """Tournament-table points for a two-sided contest (e.g. 3-0, 1-1)."""

    side_a: Contestant
    side_b: Contestant
    points_a: int
    points_b: int
