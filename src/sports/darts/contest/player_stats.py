from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contestant_stats import ContestantStats


@dataclass(frozen=True, kw_only=True)
class DartsPlayerStats(ContestantStats):
    contestant_id: str
    sets_won: int = 0
    legs_won: int = 0
    darts_thrown: int = 0
    highest_checkout: int = 0

    @property
    def subject_id(self) -> str:
        return self.contestant_id

    def with_set_won(self) -> DartsPlayerStats:
        return DartsPlayerStats(
            contestant_id=self.contestant_id,
            sets_won=self.sets_won + 1,
            legs_won=self.legs_won,
            darts_thrown=self.darts_thrown,
            highest_checkout=self.highest_checkout,
        )

    def with_leg_won(self) -> DartsPlayerStats:
        return DartsPlayerStats(
            contestant_id=self.contestant_id,
            sets_won=self.sets_won,
            legs_won=self.legs_won + 1,
            darts_thrown=self.darts_thrown,
            highest_checkout=self.highest_checkout,
        )

    def with_dart_thrown(self, points: int) -> DartsPlayerStats:
        checkout = max(self.highest_checkout, points if points > 0 else 0)
        return DartsPlayerStats(
            contestant_id=self.contestant_id,
            sets_won=self.sets_won,
            legs_won=self.legs_won,
            darts_thrown=self.darts_thrown + 1,
            highest_checkout=checkout,
        )
