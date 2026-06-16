from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.metrics import SideMetrics


@dataclass(frozen=True, kw_only=True)
class DartsContestantMetrics:
    contestant_id: str
    sets_won: int
    legs_won: int
    darts_thrown: int
    highest_checkout: int


@dataclass(frozen=True, kw_only=True)
class DartsSideMetrics(SideMetrics):
    by_contestant_id: dict[str, DartsContestantMetrics]
    decided_by: str = "regulation"


@dataclass(frozen=True, kw_only=True)
class DartsResult(ContestResult):
    ranking_entries: tuple[RankedEntry, ...]
    side: DartsSideMetrics

    def is_finished(self) -> bool:
        return bool(self.ranking_entries)

    def ranking(self) -> tuple[RankedEntry, ...]:
        return self.ranking_entries

    def side_metrics(self) -> SideMetrics:
        return self.side

    @property
    def decided_by(self) -> str:
        return self.side.decided_by

    @property
    def sets_won(self) -> dict[str, int]:
        return {
            cid: metrics.sets_won
            for cid, metrics in self.side.by_contestant_id.items()
        }

    @property
    def legs_won(self) -> dict[str, int]:
        return {
            cid: metrics.legs_won
            for cid, metrics in self.side.by_contestant_id.items()
        }
