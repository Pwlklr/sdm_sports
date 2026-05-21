from __future__ import annotations

from datetime import datetime

import pytest

from src.core.contest_event import ContestEvent


class DummyEvent(ContestEvent):
    """Concrete dummy event for testing the abstract base behavior."""
    pass


def test_contest_event_creation():
    event = DummyEvent(competitor_id="Player1", team_id="TeamA")

    assert event.competitor_id == "Player1"
    assert event.team_id == "TeamA"
    assert isinstance(event.occurred_at, datetime)
    assert event.event_id is not None
