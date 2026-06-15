from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class Event:
    """Immutable fact describing something that has already occurred in a contest."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.now)
    caused_by: str | None = None


@dataclass(frozen=True, kw_only=True)
class EventReversed(Event):
    """Compensating fact: records that an earlier event was withdrawn (e.g. VAR)."""

    target_event_id: str
    reason: str = "reversed"


ContestEvent = Event
