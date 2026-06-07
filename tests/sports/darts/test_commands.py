import pytest
from typing import Any
from src.core.contest import Contest
from src.core.ruleset import RuleSet
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.sports.darts.commands import ThrowDartCommand
from src.sports.darts.events import DartThrownEvent
from src.sports.darts.state import DartsContestState
from src.sports.darts.player import DartPlayer

class SpyRuleSet(RuleSet):
    """A minimal ruleset that just captures events for assertions."""
    
    def _dummy(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        return []

    # Satisfies the strict metaclass enforcement in RuleSet.__init_subclass__
    handlers: dict[Any, Any] = {
        DartThrownEvent: _dummy
    }

    def __init__(self) -> None:
        super().__init__()
        self.received_events: list[ContestEvent] = []

    def evaluate(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        self.received_events.append(event)
        return []

def test_throw_dart_command_dispatches_event() -> None:
    # Arrange: Use real objects to completely avoid Mock spec AttributeErrors
    p1 = DartPlayer("p1", "Player 1")
    state = DartsContestState(players=[p1], starting_score=501)
    spy_ruleset = SpyRuleSet()
    contest = Contest(contestants=[p1], initial_state=state, ruleset=spy_ruleset, contest_id="C1")
    
    command = ThrowDartCommand(sector=20, multiplier=3)
    
    # Act
    command.execute(contest)
    
    # Assert
    assert len(spy_ruleset.received_events) == 1
    called_event = spy_ruleset.received_events[0]
    
    assert isinstance(called_event, DartThrownEvent)
    assert called_event.dart_throw.points == 60