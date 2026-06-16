from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.contest.metrics import SideMetrics
from src.core.contestant.models import Contestant


@dataclass(frozen=True, kw_only=True)
class RankedEntry:
    contestant: Contestant
    place: int


class ContestResult(ABC):
    """Published snapshot of a finished contest: ranking + side_metrics."""

    @abstractmethod
    def is_finished(self) -> bool:
        pass

    @abstractmethod
    def ranking(self) -> tuple[RankedEntry, ...]:
        pass

    @abstractmethod
    def side_metrics(self) -> SideMetrics:
        pass
