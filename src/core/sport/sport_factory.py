from __future__ import annotations

from typing import Any, List, Protocol

from src.core.contest import Contest
from src.core.contestant.models import Contestant


class SportFactory(Protocol):
    """Builds a fully wired contest aggregate for a sport."""

    def create_contest(self, contestants: List[Contestant], config: Any) -> Contest: ...
