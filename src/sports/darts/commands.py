from src.core.commands import MatchCommand
from src.core.contest import Contest
from src.sports.darts.events import DartThrownEvent, MatchStarted, OcheFaultEvent
from src.sports.darts.entities import DartThrow
from src.sports.darts.state import DartsContestState

class StartDartsMatchCommand(MatchCommand):
    """Initializes the match and triggers the opening lifecycle events."""
    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, DartsContestState)
        
        if not state.is_completed and state.current_turn is None:
            match.process_event(MatchStarted())

class ThrowDartCommand(MatchCommand):
    """Translates a user's throw input into a domain event."""
    def __init__(self, sector: int, multiplier: int = 1) -> None:
        self.sector = sector
        self.multiplier = multiplier

    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, DartsContestState)
        
        if state.is_completed:
            return
            
        player = state.current_player
        throw = DartThrow(self.sector, self.multiplier)
        event = DartThrownEvent(player, throw)
        
        match.process_event(event)

class OcheFaultCommand(MatchCommand):
    """Translates a referee/player foul call into a domain event."""
    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, DartsContestState)
        
        if state.is_completed:
            return
            
        player = state.current_player
        match.process_event(OcheFaultEvent(player))