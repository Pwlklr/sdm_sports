from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, Dict, List, Optional

from src.core.contest.event import Event
from src.core.contest.contest_state import ContestState
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

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.core.contestant.models import Team
    from src.sports.football.contest.football_match_config import FootballMatchConfig
    from src.sports.football.contest.roster_status import PlayerRosterStatus


class MatchPhase(Enum):
    REGULATION = "Regulation"
    EXTRA_TIME = "Extra Time"
    PENALTIES = "Penalties"
    COMPLETED = "Completed"


class FootballContestState(ContestState):
    """Football match data mutated exclusively through apply(fact)."""

    _appliers: ClassVar[
        dict[type[Event], Callable[["FootballContestState", Event], None]]
    ] = {}

    def __init__(
        self,
        teams: List[Contestant],
        config: Optional[FootballMatchConfig] = None,
        number_of_halves: int = 2,
        half_length_minutes: int = 45,
        allow_draw: bool = True,
    ) -> None:
        super().__init__()
        if len(teams) != 2:
            raise ValueError("A football match requires exactly two sides.")

        self.teams = teams
        self.config = config

        if config:
            self.number_of_halves = config.number_of_halves
            self.half_length_minutes = config.half_length_minutes
            self.allow_draw = config.allow_draw
            self.extra_time_halves = config.extra_time_halves
            self.extra_time_half_length = config.extra_time_half_length
            self.penalty_shootout_rounds = config.penalty_shootout_rounds
            self.yellows_per_dismissal = config.yellows_per_dismissal
            self.golden_goal = config.golden_goal
            self.players_on_pitch = config.players_on_pitch
            self.min_players_on_pitch = config.min_players_on_pitch
            self.max_substitutions = config.max_substitutions
        else:
            self.number_of_halves = number_of_halves
            self.half_length_minutes = half_length_minutes
            self.allow_draw = allow_draw
            self.extra_time_halves = 2
            self.extra_time_half_length = 15
            self.penalty_shootout_rounds = 5
            self.yellows_per_dismissal = 2
            self.golden_goal = False
            self.players_on_pitch = 11
            self.min_players_on_pitch = 7
            self.max_substitutions = 5

        self.scores: Dict[str, int] = {t.id: 0 for t in teams}
        self.lineups: Dict[str, MatchLineup] = {}
        self.penalty_scores: Dict[str, int] = {t.id: 0 for t in teams}
        self.penalty_attempts: Dict[str, int] = {t.id: 0 for t in teams}
        self.disciplinary = DisciplinaryRecord()

        self.periods: List[MatchPeriod] = []
        self.current_period_idx: int = -1
        self.phase: MatchPhase = MatchPhase.REGULATION
        self.match_started: bool = False

        self.winner: Optional[Contestant] = None
        self.was_draw: bool = False
        self.decided_by: str = "regulation"
        self.is_completed: bool = False

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

    def _start_period(self, kind: PeriodKind, index: int) -> None:
        length = (
            self.half_length_minutes
            if kind == PeriodKind.REGULAR
            else self.extra_time_half_length
        )
        period = MatchPeriod(index=index, length_minutes=length, kind=kind)
        self.periods.append(period)
        self.current_period_idx = len(self.periods) - 1

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

    def roster_status(self, team: Team) -> list[PlayerRosterStatus]:
        from src.sports.football.contest.roster_status import roster_status_for_team

        return roster_status_for_team(self, team)

    def apply(self, fact: Event) -> None:
        handler = self._appliers.get(type(fact))
        if handler:
            handler(self, fact)


def _apply_match_started(state: FootballContestState, fact: Event) -> None:
    state.match_started = True


def _apply_period_started(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, PeriodStarted)
    state._start_period(fact.kind, fact.index)


def _apply_goal_scored(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, GoalScored)
    state.scores[fact.team_id] += 1
    period = state.current_period
    if period is not None:
        period.add_goal(
            Goal(
                team_id=fact.team_id,
                scorer_id=fact.scorer_id,
                minute=fact.minute,
                own_goal=fact.own_goal,
                penalty=fact.penalty,
            )
        )


def _apply_player_cautioned(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, PlayerCautioned)
    state.disciplinary.record_yellow(fact.offender_id)


def _apply_player_dismissed(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, PlayerDismissed)
    state.disciplinary.dismiss(fact.offender_id)


def _apply_period_ended(state: FootballContestState, fact: Event) -> None:
    period = state.current_period
    if period is not None:
        period.end()


def _apply_extra_time_started(state: FootballContestState, fact: Event) -> None:
    state.phase = MatchPhase.EXTRA_TIME


def _apply_penalty_shootout_started(state: FootballContestState, fact: Event) -> None:
    state.phase = MatchPhase.PENALTIES


def _apply_penalty_kick_taken(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, PenaltyKickTaken)
    state.penalty_attempts[fact.team_id] += 1
    if fact.scored:
        state.penalty_scores[fact.team_id] += 1


def _apply_match_concluded(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, MatchConcluded)
    state.was_draw = fact.draw
    state.decided_by = fact.decided_by
    state.phase = MatchPhase.COMPLETED
    state.is_completed = True
    if fact.winner_id is not None:
        state.winner = state.team_by_id(fact.winner_id)


def _apply_lineup_submitted(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, LineupSubmitted)
    state.lineups[fact.team_id] = MatchLineup(set(fact.starting), set(fact.bench))


def _apply_player_substituted(state: FootballContestState, fact: Event) -> None:
    assert isinstance(fact, PlayerSubstituted)
    lineup = state.lineups.get(fact.team_id)
    if lineup is not None:
        lineup.substitute(fact.player_out, fact.player_in)


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
