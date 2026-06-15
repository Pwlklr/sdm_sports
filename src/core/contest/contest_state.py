from __future__ import annotations

from typing import Protocol
from typing_extensions import Self

from src.core.contest.event import Event
from src.core.contestant.models import Contestant


class ContestState(Protocol):
    """Event-sourced projection: data changed exclusively through apply(fact)."""

    @property
    def is_finished(self) -> bool: ...

    @property
    def contestants(self) -> list[Contestant]: ...

    def apply(self, fact: Event) -> Self: ...

    def reset(self) -> Self: ...
