from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from src.core.contest.contest_result import ContestResult
from src.core.contestant.models import Contestant
from src.core.tournament.match_outcome import HeadToHeadPoints

if TYPE_CHECKING:
    from src.core.contest.contest import Contest


class TournamentResultReader(ABC):
    """Translates sport-specific ContestResult values into tournament vocabulary."""

    @abstractmethod
    def read_head_to_head(
        self, contest: Contest, result: ContestResult
    ) -> Optional[HeadToHeadPoints]:
        pass

    @abstractmethod
    def read_knockout_winner(
        self, contest: Contest, result: ContestResult
    ) -> Optional[Contestant]:
        pass

    @abstractmethod
    def describe_result(self, contest: Contest, result: ContestResult) -> str:
        pass


class NullTournamentResultReader(TournamentResultReader):
    def read_head_to_head(
        self, contest: Contest, result: ContestResult
    ) -> Optional[HeadToHeadPoints]:
        return None

    def read_knockout_winner(
        self, contest: Contest, result: ContestResult
    ) -> Optional[Contestant]:
        return None

    def describe_result(self, contest: Contest, result: ContestResult) -> str:
        return "zakonczony"
