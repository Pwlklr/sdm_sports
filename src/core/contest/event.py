from __future__ import annotations

from dataclasses import dataclass

from src.core.event import Event

__all__ = [
    "ContestEvent",
    "Event",
    "EventReversed",
    "OfficialOverrideEvent",
    "ProjectionEvent",
]


@dataclass(frozen=True, kw_only=True)
class ContestEvent(Event):
    """Base class for all contest-level domain events."""


@dataclass(frozen=True, kw_only=True)
class ProjectionEvent(ContestEvent):
    """Pitch fact — mutates current_state through State.apply."""


@dataclass(frozen=True, kw_only=True)
class OfficialOverrideEvent(ContestEvent):
    """Administrative decision — audit log only; interpreted on read."""


@dataclass(frozen=True, kw_only=True)
class EventReversed(ContestEvent):
    """Compensating fact: records that an earlier event was withdrawn (e.g. VAR)."""

    target_event_id: str
    reason: str = "reversed"
