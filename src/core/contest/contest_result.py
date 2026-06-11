from __future__ import annotations

from typing import Optional

from src.core.contest.result import Result
from src.core.contestant.models import Contestant


class ContestResult(Result):
    """Official result view for a contest; preserves the played outcome when overridden."""

    def __init__(self) -> None:
        self._played: Result | None = None
        self._official: Result | None = None
        self.override_reason: str | None = None

    @property
    def played(self) -> Result | None:
        return self._played

    @property
    def is_overridden(self) -> bool:
        return self._official is not None

    def record_played(self, result: Result) -> None:
        if self._played is None:
            self._played = result

    def reset_played(self) -> None:
        self._played = None

    def apply_override(self, result: Result, reason: str) -> None:
        self._official = result
        self.override_reason = reason

    @property
    def effective_result(self) -> Result | None:
        if self._official is not None:
            return self._official
        return self._played

    def is_finished(self) -> bool:
        effective = self.effective_result
        return effective is not None and effective.is_finished()


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

    @property
    def was_draw(self) -> bool:
        return self._draw

    def is_finished(self) -> bool:
        return self._draw or self._winner is not None

    def get_winner(self) -> Optional[Contestant]:
        return None if self._draw else self._winner
