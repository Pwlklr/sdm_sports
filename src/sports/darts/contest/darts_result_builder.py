from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.contest_state import ContestState
from src.core.contest.event import OfficialOverrideEvent
from src.core.contest.result_builder import ResultBuilder
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_result import (
    DartsContestantMetrics,
    DartsResult,
    DartsSideMetrics,
)
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.events import ContestResultOverridden


@dataclass(frozen=True, kw_only=True)
class DartsResultBuilder(ResultBuilder):
    config: DartsMatchConfig

    def build(self, state: ContestState) -> ContestResult:
        darts_state = _require_darts_state(state)
        if not darts_state.is_finished:
            raise ValueError("Match is not finished.")
        return self._build_from_state(darts_state)

    def build_official(
        self, state: ContestState, override: OfficialOverrideEvent
    ) -> ContestResult:
        darts_state = _require_darts_state(state)
        if not darts_state.is_finished:
            raise ValueError("Match is not finished.")
        if not isinstance(override, ContestResultOverridden):
            raise TypeError("Expected ContestResultOverridden.")
        return self._build_official_from_state(darts_state, override)

    def _build_from_state(self, state: DartsContestState) -> DartsResult:
        side = self._build_side(state, decided_by=state.decided_by)
        ranking = self._build_ranking(state)
        return DartsResult(ranking_entries=ranking, side=side)

    def _build_official_from_state(
        self, state: DartsContestState, override: ContestResultOverridden
    ) -> DartsResult:
        winner = state.player_by_id(override.winner_id)
        if winner is None:
            raise ValueError("Override winner not found in match.")
        side = self._build_side(state, decided_by=override.reason)
        return DartsResult(
            ranking_entries=self._ranking_with_winner(state, winner),
            side=side,
        )

    def _build_side(
        self, state: DartsContestState, *, decided_by: str
    ) -> DartsSideMetrics:
        return DartsSideMetrics(
            by_contestant_id={
                player_id: DartsContestantMetrics(
                    contestant_id=stats.contestant_id,
                    sets_won=stats.sets_won,
                    legs_won=stats.legs_won,
                    darts_thrown=stats.darts_thrown,
                    highest_checkout=stats.highest_checkout,
                )
                for player_id, stats in state.contestant_stats.items()
            },
            decided_by=decided_by,
        )

    def _build_ranking(self, state: DartsContestState) -> tuple[RankedEntry, ...]:
        if state.winner_id is None:
            return ()
        winner = state.player_by_id(state.winner_id)
        if winner is None:
            return ()
        return self._ranking_with_winner(state, winner)

    def _ranking_with_winner(
        self, state: DartsContestState, winner
    ) -> tuple[RankedEntry, ...]:
        entries = [RankedEntry(contestant=winner, place=1)]
        for player in state.players:
            if player.id != winner.id:
                entries.append(RankedEntry(contestant=player, place=2))
        return tuple(entries)


def _require_darts_state(state: ContestState) -> DartsContestState:
    if not isinstance(state, DartsContestState):
        raise TypeError("Expected DartsContestState.")
    return state
