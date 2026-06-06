from __future__ import annotations
from typing import TYPE_CHECKING
from src.core.contest_event import ContestEvent

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.sports.darts.entities import DartThrow

class DartsEvent(ContestEvent):
    """Base class for all darts-specific domain events."""
    pass

class MatchStarted(DartsEvent): pass
class SetStarted(DartsEvent): pass
class LegStarted(DartsEvent): pass

class TurnStarted(DartsEvent):
    def __init__(self, player: Contestant) -> None:
        super().__init__()
        self.player = player

class DartThrownEvent(DartsEvent):
    def __init__(self, player: Contestant, dart_throw: DartThrow) -> None:
        super().__init__()
        self.player = player
        self.dart_throw = dart_throw

class ScoreBusted(DartsEvent):
    def __init__(self, player: Contestant) -> None:
        super().__init__()
        self.player = player

class TurnEnded(DartsEvent):
    def __init__(self, player: Contestant) -> None:
        super().__init__()
        self.player = player

class LegWon(DartsEvent):
    def __init__(self, player: Contestant) -> None:
        super().__init__()
        self.player = player

class SetWon(DartsEvent):
    def __init__(self, player: Contestant) -> None:
        super().__init__()
        self.player = player

class MatchEnded(DartsEvent):
    def __init__(self, winner: Contestant) -> None:
        super().__init__()
        self.winner = winner