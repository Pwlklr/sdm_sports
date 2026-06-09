from __future__ import annotations

from typing import Optional

from src.core.contest.event import Event
from src.core.contestant.models import Contestant, Team
from src.core.contest.rule_set import RuleSet
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    TakePenaltyKick,
)
from src.sports.football.contest.entities import PeriodKind
from src.sports.football.contest.events import (
    ExtraTimeStarted,
    GoalScored,
    MatchConcluded,
    MatchStarted,
    PenaltyKickTaken,
    PenaltyShootoutStarted,
    PeriodEnded,
    PeriodStarted,
    PlayerCautioned,
    PlayerDismissed,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.roster import match_clock_limit, player_on_team
from src.sports.football.contest.state import FootballContestState, MatchPhase


class FootballRuleSet(RuleSet):
    def __init__(self, config: FootballMatchConfig) -> None:
        self._config = config

    def decide_start_match(
        self, command: StartMatch, state: FootballContestState
    ) -> list[Event]:
        if state.is_completed or state.match_started:
            return []
        return [
            MatchStarted(),
            PeriodStarted(kind=PeriodKind.REGULAR, index=0),
        ]

    def decide_score_goal(
        self, command: ScoreGoal, state: FootballContestState
    ) -> list[Event]:
        if state.is_completed or state.phase == MatchPhase.PENALTIES:
            return []
        period = state.current_period
        if period is None or period.is_finished:
            return []

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            return []
        if command.scorer_id is not None and not player_on_team(team, command.scorer_id):
            return []
        if not _valid_minute(command.minute, state):
            return []
        credited = state.opponent_of(team) if command.own_goal else team
        return [
            GoalScored(
                team_id=credited.id,
                scorer_id=command.scorer_id,
                minute=command.minute,
                own_goal=command.own_goal,
                penalty=command.penalty,
            )
        ]

    def decide_commit_foul(
        self, command: CommitFoul, state: FootballContestState
    ) -> list[Event]:
        if state.is_completed:
            return []

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            return []

        if command.card in {"yellow", "red"}:
            if command.offender_id is None:
                return []
            if not player_on_team(team, command.offender_id):
                return []
            if state.disciplinary.is_dismissed(command.offender_id):
                return []
            if not _valid_minute(command.minute, state):
                return []
            if command.card == "red":
                return [
                    PlayerDismissed(
                        team_id=team.id,
                        offender_id=command.offender_id,
                        minute=command.minute,
                    )
                ]
            return [
                PlayerCautioned(
                    team_id=team.id,
                    offender_id=command.offender_id,
                    minute=command.minute,
                )
            ]
        return []

    def decide_end_period(
        self, command: EndPeriod, state: FootballContestState
    ) -> list[Event]:
        if state.is_completed or state.phase == MatchPhase.PENALTIES:
            return []
        period = state.current_period
        if period is None or period.is_finished:
            return []
        return [PeriodEnded(kind=period.kind)]

    def decide_take_penalty_kick(
        self, command: TakePenaltyKick, state: FootballContestState
    ) -> list[Event]:
        if state.is_completed or state.phase != MatchPhase.PENALTIES:
            return []
        team = state.teams[command.team_index]
        return [PenaltyKickTaken(team_id=team.id, scored=command.scored)]

    def react_goal_scored(
        self, fact: GoalScored, state: FootballContestState
    ) -> list[Event]:
        if state.phase != MatchPhase.EXTRA_TIME or not state.golden_goal:
            return []
        leader = state.leading_team()
        if leader is None:
            return []
        return [
            MatchConcluded(
                winner_id=leader.id,
                draw=False,
                decided_by="golden_goal",
            )
        ]

    def react_player_cautioned(
        self, fact: PlayerCautioned, state: FootballContestState
    ) -> list[Event]:
        if state.disciplinary.is_dismissed(fact.offender_id):
            return []
        if (
            state.disciplinary.yellows_for(fact.offender_id)
            >= state.yellows_per_dismissal
        ):
            return [
                PlayerDismissed(
                    team_id=fact.team_id,
                    offender_id=fact.offender_id,
                    minute=fact.minute,
                )
            ]
        return []

    def react_period_ended(
        self, fact: PeriodEnded, state: FootballContestState
    ) -> list[Event]:
        if state.phase == MatchPhase.REGULATION:
            if state.count_periods(PeriodKind.REGULAR) < state.number_of_halves:
                return [
                    PeriodStarted(
                        kind=PeriodKind.REGULAR,
                        index=state.count_periods(PeriodKind.REGULAR),
                    )
                ]
            return _after_regulation(state)

        if state.phase == MatchPhase.EXTRA_TIME:
            if state.count_periods(PeriodKind.EXTRA_TIME) < state.extra_time_halves:
                return [
                    PeriodStarted(
                        kind=PeriodKind.EXTRA_TIME,
                        index=state.count_periods(PeriodKind.EXTRA_TIME),
                    )
                ]
            return _after_extra_time(state)

        return []

    def react_penalty_kick_taken(
        self, fact: PenaltyKickTaken, state: FootballContestState
    ) -> list[Event]:
        winner = _shootout_winner(state)
        if winner is None:
            return []
        return [
            MatchConcluded(
                winner_id=winner.id,
                draw=False,
                decided_by="penalties",
            )
        ]

    command_handlers = {
        StartMatch: decide_start_match,
        ScoreGoal: decide_score_goal,
        CommitFoul: decide_commit_foul,
        EndPeriod: decide_end_period,
        TakePenaltyKick: decide_take_penalty_kick,
    }

    reaction_handlers = {
        GoalScored: react_goal_scored,
        PlayerCautioned: react_player_cautioned,
        PeriodEnded: react_period_ended,
        PenaltyKickTaken: react_penalty_kick_taken,
    }


def _valid_minute(minute: int, state: FootballContestState) -> bool:
    return 0 <= minute <= match_clock_limit(state)


def _after_regulation(state: FootballContestState) -> list[Event]:
    if not state.is_draw or state.allow_draw:
        winner = state.leading_team()
        return [
            MatchConcluded(
                winner_id=winner.id if winner else None,
                draw=winner is None,
                decided_by="regulation",
            )
        ]

    if state.extra_time_halves > 0:
        return [
            ExtraTimeStarted(),
            PeriodStarted(kind=PeriodKind.EXTRA_TIME, index=0),
        ]

    return [PenaltyShootoutStarted()]


def _after_extra_time(state: FootballContestState) -> list[Event]:
    if not state.is_draw:
        winner = state.leading_team()
        assert winner is not None
        return [
            MatchConcluded(
                winner_id=winner.id,
                draw=False,
                decided_by="extra_time",
            )
        ]

    return [PenaltyShootoutStarted()]


def _shootout_winner(state: FootballContestState) -> Contestant | None:
    first, second = state.teams[0], state.teams[1]
    attempts_a = state.penalty_attempts[first.id]
    attempts_b = state.penalty_attempts[second.id]
    score_a = state.penalty_scores[first.id]
    score_b = state.penalty_scores[second.id]
    rounds = state.penalty_shootout_rounds

    if attempts_a <= rounds and attempts_b <= rounds:
        remaining_a = max(rounds - attempts_a, 0)
        remaining_b = max(rounds - attempts_b, 0)
        if score_a - score_b > remaining_b:
            return first
        if score_b - score_a > remaining_a:
            return second

    if attempts_a == attempts_b and attempts_a >= rounds and score_a != score_b:
        return first if score_a > score_b else second

    return None
