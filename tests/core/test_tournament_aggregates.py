import pytest
from src.core.contestant import IndividualPlayer
from src.core.contest import Contest
from src.core.contest_state import ContestState
from src.core.ruleset import RuleSet
from src.core.contest_event import ContestEvent
from src.core.tournament_aggregates import (
    TournamentRegistration, TournamentScheduler, TournamentDisciplinaryBoard
)
from src.core.tournament_event import (
    RegistrationOpened, PlayerRegistered, RegistrationClosed, MatchScheduled
)

class DummyState(ContestState): pass

class DummyEvent(ContestEvent): pass

def dummy_handler(ruleset: RuleSet, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
    return []

class DummyRuleSet(RuleSet):
    # Satisfy the strict __init_subclass__ requirement
    handlers = {DummyEvent: dummy_handler}
    
    def evaluate(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        return []

def test_tournament_registration_lifecycle() -> None:
    reg = TournamentRegistration()
    p1 = IndividualPlayer("P1")
    
    # Cannot register while closed
    with pytest.raises(ValueError):
        reg.register(p1)
        
    # Open registration
    events = reg.open_registration()
    assert isinstance(events[0], RegistrationOpened)
    assert reg.is_open is True
    
    # Register player
    events = reg.register(p1)
    assert isinstance(events[0], PlayerRegistered)
    assert len(reg.registered_contestants) == 1
    
    # Cannot double register
    with pytest.raises(ValueError):
        reg.register(p1)
        
    # Close registration
    events = reg.close_registration()
    assert isinstance(events[0], RegistrationClosed)
    assert reg.is_open is False

def test_tournament_scheduler() -> None:
    scheduler = TournamentScheduler()
    match = Contest([], DummyState(), DummyRuleSet())
    
    events = scheduler.schedule_match(match)
    assert isinstance(events[0], MatchScheduled)
    assert len(scheduler.pending_matches) == 1
    
    next_match = scheduler.pop_next_match()
    assert next_match == match
    assert len(scheduler.pending_matches) == 0
    assert scheduler.pop_next_match() is None

def test_tournament_disciplinary_board() -> None:
    board = TournamentDisciplinaryBoard()
    p1 = IndividualPlayer("P1")
    
    board.log_infraction(p1, "Yellow Card")
    board.log_infraction(p1, "Foul")
    
    assert len(board.records[p1.id]) == 2
    assert board.records[p1.id] == ["Yellow Card", "Foul"]