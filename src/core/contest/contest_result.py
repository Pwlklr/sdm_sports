from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

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


@dataclass(frozen=True, kw_only=True)
class EmptySideMetrics:
    """Minimal side metrics for overrides without played data."""


class OfficialResultView:
    """Official result view for a contest; preserves played outcome when overridden."""

    def __init__(self) -> None:
        self._played: ContestResult | None = None
        self._official: ContestResult | None = None
        self.override_reason: str | None = None

    @property
    def played(self) -> ContestResult | None:
        return self._played

    @property
    def is_overridden(self) -> bool:
        return self._official is not None

    def record_played(self, result: ContestResult) -> None:
        if self._played is None:
            self._played = result

    def reset_played(self) -> None:
        self._played = None

    def apply_override(self, result: ContestResult, reason: str) -> None:
        self._official = result
        self.override_reason = reason

    @property
    def effective_result(self) -> ContestResult | None:
        if self._official is not None:
            return self._official
        return self._played

    def is_finished(self) -> bool:
        effective = self.effective_result
        return effective is not None and effective.is_finished()


@dataclass(frozen=True, kw_only=True)
class ContestOutcome(ContestResult):
    """Minimal result not built from replayed events (walkover, forfeit, commission)."""

    winner: Optional[Contestant]
    draw: bool = False
    decided_by: str = "override"

    def is_finished(self) -> bool:
        return self.draw or self.winner is not None

    def ranking(self) -> tuple[RankedEntry, ...]:
        if self.draw and self.winner is not None:
            return (RankedEntry(contestant=self.winner, place=1),)
        if self.draw:
            return ()
        if self.winner is not None:
            return (RankedEntry(contestant=self.winner, place=1),)
        return ()

    def side_metrics(self) -> SideMetrics:
        return EmptySideMetrics()
