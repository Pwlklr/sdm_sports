from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.contest.contest_result import ContestResult
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event, OfficialOverrideEvent


class ResultBuilder(ABC):
    """Builds a sport-specific ContestResult from the current projection and event history.

    Builders receive both the current state projection *and* the full event history.
    This lets them read concluding events (e.g. MatchConcluded) directly from the log
    rather than relying on result-metadata fields being cached in the state.
    """

    @abstractmethod
    def build(self, state: ContestState, history: list[Event]) -> ContestResult:
        pass

    @abstractmethod
    def build_official(
        self,
        state: ContestState,
        history: list[Event],
        override: OfficialOverrideEvent,
    ) -> ContestResult:
        pass
