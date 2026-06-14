from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.core.contest.contest_result import ContestResult
    from src.core.contest.contest_state import ContestState


class ResultBuilder(Protocol):
    """Builds a sport-specific ContestResult snapshot from the current projection."""

    def build(self, state: ContestState) -> ContestResult: ...
