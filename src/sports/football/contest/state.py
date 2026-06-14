from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import ClassVar, Optional

from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event
from src.core.contestant.models import Contestant, Team
from src.sports.football.contest.entities import (
    DisciplinaryRecord,
    Goal,
    MatchLineup,
    MatchPeriod,
    PeriodKind,
)
from src.sports.football.contest.events import (
    ExtraTimeStarted,
    GoalScored,
    LineupSubmitted,
    MatchConcluded,
    MatchStarted,
    PenaltyKickTaken,
    PenaltyShootoutStarted,
    PeriodEnded,
    PeriodStarted,
    PlayerCautioned,
    PlayerDismissed,
    PlayerSubstituted,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.player_stats import FootballPlayerStats, init_player_stats_for_teams

if False:
    from src.sports.football.contest.roster_status import PlayerRosterStatus


class MatchPhase(Enum):
    REGULATION = "Regulation"
    EXTRA_TIME = "Extra Time"
    PENALTIES = "Penalties"
    COMPLETED = "Completed"


@dataclass(frozen=True, kw_only=True)
class FootballContestState:
    """Football match projection updated exclusively through apply(fact)."""

    teams: tuple[Team, Team]
    config: FootballMatchConfig
    suspended_player_ids: frozenset[str] = frozenset()
    scores: dict[str, int] = field(default_factory=dict)
    lineups: dict[str, MatchLineup] = field(default_factory=dict)
    penalty_scores: dict[str, int] = field(default_factory=dict)
    penalty_attempts: dict[str, int] = field(default_factory=dict)
    disciplinary: DisciplinaryRecord = field(default_factory=DisciplinaryRecord)
    player_stats: dict[str, FootballPlayerStats] = field(default_factory=dict)
    periods: tuple[MatchPeriod, ...] = ()
    current_period_idx: int = -1
    phase: MatchPhase = MatchPhase.REGULATION
    match_started: bool = False
    winner: Optional[Contestant] = None
    was_draw: bool = False
    decided_by: str = "regulation"
    is_finished: bool = False

    _appliers: ClassVar[
        dict[type[Event], Callable[["FootballContestState", Event], FootballContestState]]
    ] = {}

    def __post_init__(self) -> None:
        if len(self.teams) != 2:
            raise ValueError("A football match requires exactly two sides.")
        for side in self.teams:
            if not isinstance(side, Team):
                raise ValueError("Football matches require Team contestants.")

    @property
    def contestants(self) -> list[Contestant]:
        return list(self.teams)

    @property
    def current_period(self) -> Optional[MatchPeriod]:
        if 0 <= self.current_period_idx < len(self.periods):
            return self.periods[self.current_period_idx]
        return None

    def team_by_id(self, team_id: str) -> Optional[Contestant]:
        for team in self.teams:
            if team.id == team_id:
                return team
        return None

    def is_suspended(self, player_id: str) -> bool:
        return player_id in self.suspended_player_ids

    def lineup_for(self, team_id: str) -> Optional[MatchLineup]:
        return self.lineups.get(team_id)

    def active_players_on_pitch(self, team_id: str) -> int:
        lineup = self.lineups.get(team_id)
        if lineup is None:
            return 0
        return lineup.active_on_pitch(self.disciplinary.dismissed)

    def opponent_of(self, team: Contestant) -> Contestant:
        for candidate in self.teams:
            if candidate.id != team.id:
                return candidate
        return team

    def count_periods(self, kind: PeriodKind) -> int:
        return len([p for p in self.periods if p.kind == kind])

    @property
    def is_draw(self) -> bool:
        return self.scores[self.teams[0].id] == self.scores[self.teams[1].id]

    def leading_team(self) -> Optional[Contestant]:
        first, second = self.teams[0], self.teams[1]
        if self.scores[first.id] > self.scores[second.id]:
            return first
        if self.scores[second.id] > self.scores[first.id]:
            return second
        return None

    def with_tournament_context(
        self, *, suspended_player_ids: frozenset[str]
    ) -> FootballContestState:
        return replace(self, suspended_player_ids=suspended_player_ids)

    def roster_status(self, team: Team) -> list:
        from src.sports.football.contest.roster_status import roster_status_for_team

        return roster_status_for_team(self, team)

    def apply(self, fact: Event) -> FootballContestState:
        handler = self._appliers.get(type(fact))
        if handler:
            return handler(self, fact)
        return self

    def reset(self) -> FootballContestState:
        return FootballContestState(
            teams=self.teams,
            config=self.config,
            suspended_player_ids=self.suspended_player_ids,
            scores={t.id: 0 for t in self.teams},
            penalty_scores={t.id: 0 for t in self.teams},
            penalty_attempts={t.id: 0 for t in self.teams},
            player_stats=init_player_stats_for_teams(self.teams),
        )


def _start_period(
    state: FootballContestState, kind: PeriodKind, index: int
) -> FootballContestState:
    length = (
        state.config.half_length_minutes
        if kind == PeriodKind.REGULAR
        else state.config.extra_time_half_length
    )
    period = MatchPeriod(index=index, length_minutes=length, kind=kind)
    periods = state.periods + (period,)
    return replace(state, periods=periods, current_period_idx=len(periods) - 1)


def _update_player_stats(
    stats: dict[str, FootballPlayerStats], player_id: str | None, updater
) -> dict[str, FootballPlayerStats]:
    if player_id is None or player_id not in stats:
        return stats
    new_stats = dict(stats)
    new_stats[player_id] = updater(stats[player_id])
    return new_stats


def _apply_match_started(state: FootballContestState, fact: Event) -> FootballContestState:
    return replace(state, match_started=True)


def _apply_period_started(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, PeriodStarted)
    return _start_period(state, fact.kind, fact.index)


def _apply_goal_scored(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, GoalScored)
    scores = dict(state.scores)
    scores[fact.team_id] = scores.get(fact.team_id, 0) + 1
    period = state.current_period
    periods = state.periods
    if period is not None:
        updated = period.with_goal(
            Goal(
                team_id=fact.team_id,
                scorer_id=fact.scorer_id,
                minute=fact.minute,
                own_goal=fact.own_goal,
                penalty=fact.penalty,
            )
        )
        periods = (
            state.periods[: state.current_period_idx]
            + (updated,)
            + state.periods[state.current_period_idx + 1 :]
        )
    player_stats = _update_player_stats(
        state.player_stats, fact.scorer_id, lambda s: s.with_goal()
    )
    return replace(state, scores=scores, periods=periods, player_stats=player_stats)


def _apply_player_cautioned(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, PlayerCautioned)
    disciplinary = state.disciplinary.with_yellow(fact.offender_id)
    player_stats = _update_player_stats(
        state.player_stats, fact.offender_id, lambda s: s.with_yellow()
    )
    return replace(state, disciplinary=disciplinary, player_stats=player_stats)


def _apply_player_dismissed(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, PlayerDismissed)
    disciplinary = state.disciplinary.with_dismissal(fact.offender_id)
    player_stats = _update_player_stats(
        state.player_stats, fact.offender_id, lambda s: s.with_dismissed()
    )
    return replace(state, disciplinary=disciplinary, player_stats=player_stats)


def _apply_period_ended(state: FootballContestState, fact: Event) -> FootballContestState:
    period = state.current_period
    if period is None:
        return state
    updated = period.with_ended()
    periods = (
        state.periods[: state.current_period_idx]
        + (updated,)
        + state.periods[state.current_period_idx + 1 :]
    )
    return replace(state, periods=periods)


def _apply_extra_time_started(state: FootballContestState, fact: Event) -> FootballContestState:
    return replace(state, phase=MatchPhase.EXTRA_TIME)


def _apply_penalty_shootout_started(
    state: FootballContestState, fact: Event
) -> FootballContestState:
    return replace(state, phase=MatchPhase.PENALTIES)


def _apply_penalty_kick_taken(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, PenaltyKickTaken)
    attempts = dict(state.penalty_attempts)
    attempts[fact.team_id] = attempts.get(fact.team_id, 0) + 1
    scores = dict(state.penalty_scores)
    if fact.scored:
        scores[fact.team_id] = scores.get(fact.team_id, 0) + 1
    return replace(state, penalty_attempts=attempts, penalty_scores=scores)


def _apply_match_concluded(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, MatchConcluded)
    winner = state.team_by_id(fact.winner_id) if fact.winner_id is not None else None
    return replace(
        state,
        was_draw=fact.draw,
        decided_by=fact.decided_by,
        phase=MatchPhase.COMPLETED,
        is_finished=True,
        winner=winner,
    )


def _apply_lineup_submitted(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, LineupSubmitted)
    lineups = dict(state.lineups)
    lineups[fact.team_id] = MatchLineup(
        starting=frozenset(fact.starting),
        bench=frozenset(fact.bench),
    )
    return replace(state, lineups=lineups)


def _apply_player_substituted(state: FootballContestState, fact: Event) -> FootballContestState:
    assert isinstance(fact, PlayerSubstituted)
    lineup = state.lineups.get(fact.team_id)
    if lineup is None:
        return state
    lineups = dict(state.lineups)
    lineups[fact.team_id] = lineup.with_substitution(fact.player_out, fact.player_in)
    return replace(state, lineups=lineups)


FootballContestState._appliers = {
    MatchStarted: _apply_match_started,
    PeriodStarted: _apply_period_started,
    GoalScored: _apply_goal_scored,
    PlayerCautioned: _apply_player_cautioned,
    PlayerDismissed: _apply_player_dismissed,
    PeriodEnded: _apply_period_ended,
    ExtraTimeStarted: _apply_extra_time_started,
    PenaltyShootoutStarted: _apply_penalty_shootout_started,
    PenaltyKickTaken: _apply_penalty_kick_taken,
    MatchConcluded: _apply_match_concluded,
    LineupSubmitted: _apply_lineup_submitted,
    PlayerSubstituted: _apply_player_substituted,
}


def create_football_contest_state(
    teams: list[Contestant],
    config: FootballMatchConfig,
    *,
    suspended_player_ids: frozenset[str] | None = None,
) -> FootballContestState:
    if len(teams) != 2:
        raise ValueError("A football match requires exactly two sides.")
    pair = (teams[0], teams[1])
    if not isinstance(pair[0], Team) or not isinstance(pair[1], Team):
        raise ValueError("Football matches require Team contestants.")
    return FootballContestState(
        teams=pair,
        config=config,
        suspended_player_ids=suspended_player_ids or frozenset(),
        scores={t.id: 0 for t in pair},
        penalty_scores={t.id: 0 for t in pair},
        penalty_attempts={t.id: 0 for t in pair},
        player_stats=init_player_stats_for_teams(pair),
    )
