import pytest
from datetime import datetime
from src.core.events import ContestEvent

class DummyEvent(ContestEvent):
    """Concrete dummy event for testing the abstract base behavior."""
    pass

def test_contest_event_creation():
    # Arrange & Act
    event = DummyEvent(competitor_id="Player1", team_id="TeamA")
    
    # Assert
    assert event.competitor_id == "Player1"
    assert event.team_id == "TeamA"
    assert isinstance(event.occurred_at, datetime)
    assert event.event_id is not None