from dataclasses import dataclass
from src.core.contest_event import ContestEvent


@dataclass(frozen=True)
class DartThrownEvent(ContestEvent):
    """Triggered when a player throws a single dart."""

    player_id: str
    sector: int
    multiplier: int

    @property
    def points(self) -> int:
        """Calculates the total points scored by this specific dart."""
        return self.sector * self.multiplier


@dataclass(frozen=True)
class ScoreBustedEvent(ContestEvent):
    """Triggered when a player's throw breaks the scoring rules (busting)."""

    player_id: str
    reason: str


@dataclass(frozen=True)
class LegWonEvent(ContestEvent):
    """Triggered when a player legally reaches 0 points."""

    player_id: str
