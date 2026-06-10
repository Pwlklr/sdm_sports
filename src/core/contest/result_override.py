from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.contest.result import Result
from src.core.contestant.models import Contestant


@dataclass(frozen=True)
class ResultOverride:
    """Wrapper for an official result set outside the match event log.

    The sporting ``Contest.result`` and ``history`` stay intact; this only
    changes what counts in tables, tournaments and archives.
    """

    result: Result
    reason: str


class ContestOutcome(Result):
    """Minimal result not built from replayed events (walkover, forfeit, commission ruling)."""

    def __init__(
        self,
        winner: Optional[Contestant],
        *,
        draw: bool = False,
        decided_by: str = "override",
    ) -> None:
        self._winner = winner
        self._draw = draw
        self.decided_by = decided_by

    def is_finished(self) -> bool:
        return self._draw or self._winner is not None

    def get_winner(self) -> Optional[Contestant]:
        return None if self._draw else self._winner
