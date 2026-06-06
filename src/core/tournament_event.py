from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.core.contest import Contest

class TournamentEvent(ABC):
    """Base class for all tournament-level domain events."""
    pass

class RegistrationOpened(TournamentEvent): 
    pass

class PlayerRegistered(TournamentEvent):
    def __init__(self, contestant: 'Contestant') -> None:
        self.contestant = contestant

class RegistrationClosed(TournamentEvent): 
    pass

class MatchScheduled(TournamentEvent):
    def __init__(self, match: 'Contest') -> None:
        self.match = match