from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from src.core.contest.result import Result
from src.core.contestant.models import Contestant
from src.core.tournament.match_outcome import HeadToHeadPoints

if TYPE_CHECKING:
    from src.core.contest.contest import Contest


class TournamentResultReader(ABC):
    """Translates sport-specific ``Result`` values into tournament vocabulary.

    Phases and policies depend on this contract, not on concrete sport result types.
    Each sport plugin supplies an implementation.
    """

    @abstractmethod
    def read_head_to_head(
        self, contest: Contest, result: Result
    ) -> Optional[HeadToHeadPoints]:
        """Return table points for a pairwise match, or ``None`` if not applicable."""
        pass

    @abstractmethod
    def read_knockout_winner(
        self, contest: Contest, result: Result
    ) -> Optional[Contestant]:
        """Return the contestant advancing from knockout, or ``None`` (e.g. draw)."""
        pass

    @abstractmethod
    def describe_result(self, contest: Contest, result: Result) -> str:
        """Short human-readable summary for schedules and brackets."""
        pass


class NullTournamentResultReader(TournamentResultReader):
    """No-op reader for tests or phases that do not interpret match results."""

    def read_head_to_head(
        self, contest: Contest, result: Result
    ) -> Optional[HeadToHeadPoints]:
        return None

    def read_knockout_winner(
        self, contest: Contest, result: Result
    ) -> Optional[Contestant]:
        return None

    def describe_result(self, contest: Contest, result: Result) -> str:
        return "zakonczony"
