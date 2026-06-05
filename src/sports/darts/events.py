from dataclasses import dataclass
from src.core.contest_event import ContestEvent

@dataclass(frozen=True)
class DartThrownEvent(ContestEvent):
    player_id: str
    sector: int
    multiplier: int

    @property
    def points(self) -> int:
        return self.sector * self.multiplier

@dataclass(frozen=True)
class ScoreBustedEvent(ContestEvent):
    player_id: str
    reason: str

@dataclass(frozen=True)
class LegWonEvent(ContestEvent):
    player_id: str

@dataclass(frozen=True)
class SetWonEvent(ContestEvent):
    player_id: str

@dataclass(frozen=True)
class MatchEndedEvent(ContestEvent):
    winner_id: str