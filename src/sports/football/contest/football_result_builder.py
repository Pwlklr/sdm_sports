from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event, OfficialOverrideEvent
from src.core.contest.result_builder import ResultBuilder
from src.sports.football.contest.events import ContestResultOverridden, MatchConcluded
from src.sports.football.contest.football_contest_state import FootballContestState
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import (
    FootballPlayerMatchStats,
    FootballResult,
    FootballSideMetrics,
    FootballTeamSideMetrics,
)
from src.sports.football.contest.player_stats import FootballPlayerStats


@dataclass(frozen=True, kw_only=True)
class FootballResultBuilder(ResultBuilder):
    config: FootballMatchConfig

    def build(self, state: ContestState, history: list[Event]) -> ContestResult:
        football_state = _require_football_state(state)
        if not football_state.is_finished:
            raise ValueError("Match is not finished.")
        concluded = _find_match_concluded(history)
        return self._build_from_state(football_state, concluded)

    def build_official(
        self,
        state: ContestState,
        history: list[Event],
        override: OfficialOverrideEvent,
    ) -> ContestResult:
        football_state = _require_football_state(state)
        if not football_state.is_finished:
            raise ValueError("Match is not finished.")
        if not isinstance(override, ContestResultOverridden):
            raise TypeError("Expected ContestResultOverridden.")
        return self._build_official_from_state(football_state, override)

    def _build_from_state(
        self,
        state: FootballContestState,
        concluded: MatchConcluded | None,
    ) -> FootballResult:
        decided_by = concluded.decided_by if concluded else "regulation"
        side = self._build_side(state, decided_by=decided_by)
        ranking = self._build_ranking(state, concluded)
        return FootballResult(ranking_entries=ranking, side=side)

    def _build_official_from_state(
        self, state: FootballContestState, override: ContestResultOverridden
    ) -> FootballResult:
        winner = state.team_by_id(override.winner_id)
        if winner is None:
            raise ValueError("Override winner not found in match.")
        loser = state.opponent_of(winner)
        side = self._build_side(state, decided_by=override.reason)
        by_team_id: dict[str, FootballTeamSideMetrics] = {}
        for team_id, team_metrics in side.by_team_id.items():
            if team_id == winner.id:
                score = override.winner_score
            elif team_id == loser.id:
                score = override.loser_score
            else:
                score = team_metrics.score
            by_team_id[team_id] = FootballTeamSideMetrics(
                team_id=team_metrics.team_id,
                score=score,
                penalty_score=team_metrics.penalty_score,
                players=team_metrics.players,
            )
        official_side = FootballSideMetrics(
            by_team_id=by_team_id,
            decided_by=override.reason,
        )
        ranking = (
            RankedEntry(contestant=winner, place=1),
            RankedEntry(contestant=loser, place=2),
        )
        return FootballResult(ranking_entries=ranking, side=official_side)

    def _build_side(
        self, state: FootballContestState, *, decided_by: str
    ) -> FootballSideMetrics:
        by_team_id: dict[str, FootballTeamSideMetrics] = {}
        for team in state.teams:
            players = {
                player.id: _to_match_stats(state.player_stats[player.id])
                for player in team.roster
                if player.id in state.player_stats
            }
            by_team_id[team.id] = FootballTeamSideMetrics(
                team_id=team.id,
                score=state.scores.get(team.id, 0),
                penalty_score=state.penalty_scores.get(team.id, 0),
                players=players,
            )
        return FootballSideMetrics(by_team_id=by_team_id, decided_by=decided_by)

    def _build_ranking(
        self,
        state: FootballContestState,
        concluded: MatchConcluded | None,
    ) -> tuple[RankedEntry, ...]:
        team_a, team_b = state.teams[0], state.teams[1]
        is_draw = concluded.draw if concluded else (state.winner is None)
        if is_draw:
            return (
                RankedEntry(contestant=team_a, place=1),
                RankedEntry(contestant=team_b, place=1),
            )
        if state.winner is not None:
            loser = state.opponent_of(state.winner)
            return (
                RankedEntry(contestant=state.winner, place=1),
                RankedEntry(contestant=loser, place=2),
            )
        return ()


def _find_match_concluded(history: list[Event]) -> MatchConcluded | None:
    for event in reversed(history):
        if isinstance(event, MatchConcluded):
            return event
    return None


def _to_match_stats(stats: FootballPlayerStats) -> FootballPlayerMatchStats:
    return FootballPlayerMatchStats(
        player_id=stats.player_id,
        goals=stats.goals,
        yellow_cards=stats.yellow_cards,
        dismissed=stats.dismissed,
    )


def _require_football_state(state: ContestState) -> FootballContestState:
    if not isinstance(state, FootballContestState):
        raise TypeError("Expected FootballContestState.")
    return state
