from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.contest.contest_result import ContestResult
from src.core.tournament.match_outcome_snapshot import MatchOutcomeSnapshot


class PhaseOutcomeInterpreter(ABC):
    @abstractmethod
    def interpret(self, contest_id: str, result: ContestResult) -> MatchOutcomeSnapshot:
        pass
