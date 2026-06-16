from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.contest.contest_result import ContestResult
from src.core.contest.contest_state import ContestState
from src.core.contest.event import OfficialOverrideEvent


class ResultBuilder(ABC):
    """Builds a sport-specific ContestResult snapshot from the current projection."""

    @abstractmethod
    def build(self, state: ContestState) -> ContestResult:
        pass

    @abstractmethod
    def build_official(
        self, state: ContestState, override: OfficialOverrideEvent
    ) -> ContestResult:
        pass
