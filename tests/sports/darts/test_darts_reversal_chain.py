from src.core.contest.contest_state import ContestState
from src.core.contest.reversal_chain import ReversalContext
from src.core.contest.event import Event
from src.sports.darts.contest.commands import RevokeDartThrow
from src.sports.darts.contest.darts_reversal import DartsLegIntegrityHandler
from src.sports.darts.contest.events import DartScored, LegStarted, LegWon


class DummyContestState(ContestState):
    """A minimal mock state to satisfy ReversalContext requirements."""
    @property
    def is_finished(self) -> bool: return False
    @property
    def contestants(self) -> list: return []
    def apply(self, fact: Event) -> 'DummyContestState': return self
    def reset(self) -> 'DummyContestState': return self

def test_darts_leg_integrity_handler_reverses_leg_when_earlier_dart_revoked() -> None:
    """Covers the branch where event.caused_by != target.event_id"""
    # 1. Arrange Events: dart_1 is revoked, but dart_2 caused the leg win
    target_dart = DartScored(event_id="dart_1", player_id="p1", sector=20, multiplier=2, points=40)
    winning_dart = DartScored(event_id="dart_2", player_id="p1", sector=20, multiplier=2, points=40)
    
    # event.caused_by ("dart_2") != target.event_id ("dart_1"). This triggers the IF condition!
    leg_won = LegWon(event_id="win_1", player_id="p1", caused_by="dart_2") 
    next_leg = LegStarted(event_id="leg_2", starting_player_id="p2")
    
    history = [target_dart, winning_dart, leg_won, next_leg]
    
    # 2. Arrange Command and Context
    command = RevokeDartThrow(target_event_id="dart_1", reason="Oche Fault")
    ctx = ReversalContext(command=command, state=DummyContestState(), history=history)
    
    # 3. Act
    handler = DartsLegIntegrityHandler()
    handler._contribute(ctx)
    
    # 4. Assert
    assert len(ctx.markers) == 1
    assert ctx.markers[0].target_event_id == "win_1"
    assert ctx.markers[0].reason == "Oche Fault"


def test_darts_leg_integrity_handler_ignores_when_winning_dart_revoked() -> None:
    """Covers the branch where event.caused_by == target.event_id"""
    # 1. Arrange Events: dart_1 won the leg AND is the one being revoked
    target_dart = DartScored(event_id="dart_1", player_id="p1", sector=20, multiplier=2, points=40)
    
    # event.caused_by matches target.event_id. This skips the IF condition!
    leg_won = LegWon(event_id="win_1", player_id="p1", caused_by="dart_1") 
    
    history = [target_dart, leg_won]
    
    # 2. Arrange Command and Context
    command = RevokeDartThrow(target_event_id="dart_1", reason="Oche Fault")
    ctx = ReversalContext(command=command, state=DummyContestState(), history=history)
    
    # 3. Act
    handler = DartsLegIntegrityHandler()
    handler._contribute(ctx)
    
    # 4. Assert
    assert len(ctx.markers) == 0  # No marker added by THIS specific handler