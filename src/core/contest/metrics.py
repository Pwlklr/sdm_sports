from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SideMetrics(Protocol):
    """Side/contestant-level aggregates from a finished contest."""


class IndividualMetrics(Protocol):
    """Per-player aggregates nested inside side_metrics (team sports only)."""


@dataclass(frozen=True, kw_only=True)
class FootballPlayerMatchStats:
    """Player-level snapshot nested under a team side."""

    player_id: str
    goals: int
    assists: int
    yellow_cards: int
    dismissed: bool
