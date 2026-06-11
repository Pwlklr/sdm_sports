from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class Command:
    """Immutable intent issued against a contest (may be rejected by the ruleset)."""

    issued_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, kw_only=True)
class ReverseDecision(Command):
    """Intent to withdraw an earlier contest fact from the active projection."""

    target_event_id: str
    reason: str = "reversed"
