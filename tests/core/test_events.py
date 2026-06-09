from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.core.contest.event import Event


@dataclass(frozen=True, kw_only=True)
class DummyEvent(Event):
    competitor_id: str | None = None
    team_id: str | None = None


def test_event_creation() -> None:
    event = DummyEvent(competitor_id="Player1", team_id="TeamA")

    assert event.competitor_id == "Player1"
    assert event.team_id == "TeamA"
    assert isinstance(event.occurred_at, datetime)
    assert event.event_id is not None
