import pytest
from unittest.mock import MagicMock
from src.core.contest import Contest
from src.sports.darts.commands import ThrowDartCommand
from src.sports.darts.events import DartThrownEvent

def test_throw_dart_command_dispatches_event() -> None:
    # Arrange: Mock the contest so we don't need real teams/states here
    mock_contest = MagicMock(spec=Contest)
    command = ThrowDartCommand(player_id="p1", sector=20, multiplier=3)
    
    # Act
    command.execute(mock_contest)
    
    # Assert: Ensure process_event was called with the correct Domain Event
    mock_contest.process_event.assert_called_once()
    called_event = mock_contest.process_event.call_args[0][0]
    
    assert isinstance(called_event, DartThrownEvent)
    assert called_event.player_id == "p1"
    assert called_event.points == 60