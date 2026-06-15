from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.contest_state import ContestState
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_result import (
    DartsContestantMetrics,
    DartsResult,
    DartsSideMetrics,
)
from src.sports.darts.contest.darts_contest_state import DartsContestState


@dataclass(frozen=True, kw_only=True)
class DartsResultBuilder:
    config: DartsMatchConfig

    def build(self, state: ContestState) -> ContestResult:
        darts_state = _require_darts_state(state)
        if not darts_state.is_finished:
            raise ValueError("Match is not finished.")
        return self._build_from_state(darts_state)

    def _build_from_state(self, state: DartsContestState) -> DartsResult:
        side = DartsSideMetrics(
            by_contestant_id={
                player_id: DartsContestantMetrics(
                    contestant_id=stats.contestant_id,
                    sets_won=stats.sets_won,
                    legs_won=stats.legs_won,
                    darts_thrown=stats.darts_thrown,
                    highest_checkout=stats.highest_checkout,
                )
                for player_id, stats in state.contestant_stats.items()
            }
        )
        ranking = self._build_ranking(state)
        return DartsResult(ranking_entries=ranking, side=side)

    def _build_ranking(self, state: DartsContestState) -> tuple[RankedEntry, ...]:
        if state.winner_id is None:
            return ()
        winner = state.player_by_id(state.winner_id)
        if winner is None:
            return ()
        others = [p for p in state.players if p.id != state.winner_id]
        others.sort(
            key=lambda p: (
                -state.contestant_stats[p.id].sets_won,
                -state.contestant_stats[p.id].legs_won,
                p.id,
            )
        )
        entries = [RankedEntry(contestant=winner, place=1)]
        for place, player in enumerate(others, start=2):
            entries.append(RankedEntry(contestant=player, place=place))
        return tuple(entries)


def _require_darts_state(state: ContestState) -> DartsContestState:
    if not isinstance(state, DartsContestState):
        raise TypeError("Expected DartsContestState.")
    return state
