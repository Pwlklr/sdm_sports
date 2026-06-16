from __future__ import annotations

from typing import Any, Protocol

from src.core.contest.contest import Contest
from src.core.contestant.models import Contestant


class MatchProvider(Protocol):
    def create(
        self,
        sides: list[Contestant],
        *,
        match_config: Any,
        contest_id: str | None = None,
        suspended_player_ids: frozenset[str] | None = None,
    ) -> Contest: ...
