from __future__ import annotations

from typing import Optional

from src.core.contest_event import ContestEvent
from src.core.contestant import Contestant
from src.core.ruleset import RuleSet
from src.sports.football.disciplinary import (
    CautionPenalty,
    DismissalPenalty,
    FoulViolation,
)
from src.sports.football.entities import Goal, PeriodKind
from src.sports.football.events import (
    EndPeriodEvent,
    ExtraTimeStarted,
    FoulCommittedEvent,
    GoalScored,
    GoalScoredEvent,
    MatchEnded,
    PenaltyKickEvent,
    PenaltyShootoutStarted,
    PeriodEnded,
    PeriodStarted,
    PlayerCautioned,
    PlayerDismissed,
)
from src.sports.football.state import FootballContestState, MatchPhase


class FootballRuleSet(RuleSet):
    """
    Evaluates football events against the current state, enforcing the laws
    of the game: goals, cautions/dismissals, half progression, extra time
    and penalty shootouts.
    """

    def handle_goal(
        self, event: GoalScoredEvent, state: FootballContestState
    ) -> list[ContestEvent]:
        new_events: list[ContestEvent] = []

        if state.is_completed or state.phase == MatchPhase.PENALTIES:
            return new_events

        state.ensure_match_started()
        period = state.current_period
        if period is None or period.is_finished:
            return new_events

        credited = state.opponent_of(event.team) if event.own_goal else event.team
        goal = Goal(
            team_id=credited.id,
            scorer_id=event.scorer_id,
            minute=event.minute,
            own_goal=event.own_goal,
            penalty=event.penalty,
        )
        period.add_goal(goal)
        state.scores[credited.id] += goal.points

        new_events.append(GoalScored(credited))
        return new_events

    def handle_foul(
        self, event: FoulCommittedEvent, state: FootballContestState
    ) -> list[ContestEvent]:
        new_events: list[ContestEvent] = []

        if state.is_completed:
            return new_events

        offender_id = event.offender_id or event.team.id
        violation = FoulViolation(event.team, event.reason)

        if event.card == "yellow":
            caution = CautionPenalty(violation, offender_id)
            caution.apply(state.disciplinary)
            new_events.append(PlayerCautioned(event.team, offender_id))
            if caution.triggers_dismissal:
                new_events.append(PlayerDismissed(event.team, offender_id))
        elif event.card == "red":
            dismissal = DismissalPenalty(violation, offender_id)
            dismissal.apply(state.disciplinary)
            new_events.append(PlayerDismissed(event.team, offender_id))

        return new_events

    def handle_end_period(
        self, event: EndPeriodEvent, state: FootballContestState
    ) -> list[ContestEvent]:
        new_events: list[ContestEvent] = []

        if state.is_completed or state.phase == MatchPhase.PENALTIES:
            return new_events

        state.ensure_match_started()
        period = state.current_period
        assert period is not None
        period.end()
        new_events.append(PeriodEnded(period.kind.value))

        if state.phase == MatchPhase.REGULATION:
            if state.count_periods(PeriodKind.REGULAR) < state.number_of_halves:
                state.start_period(PeriodKind.REGULAR)
                new_events.append(PeriodStarted("Regular"))
                return new_events
            return _resolve_after_regulation(state, new_events)

        if state.phase == MatchPhase.EXTRA_TIME:
            if state.count_periods(PeriodKind.EXTRA_TIME) < state.extra_time_halves:
                state.start_period(PeriodKind.EXTRA_TIME)
                new_events.append(PeriodStarted("Extra Time"))
                return new_events
            return _resolve_after_extra_time(state, new_events)

        return new_events

    def handle_penalty_kick(
        self, event: PenaltyKickEvent, state: FootballContestState
    ) -> list[ContestEvent]:
        new_events: list[ContestEvent] = []

        if state.is_completed or state.phase != MatchPhase.PENALTIES:
            return new_events

        state.penalty_attempts[event.team.id] += 1
        if event.scored:
            state.penalty_scores[event.team.id] += 1

        winner = state.penalty_shootout_winner()
        if winner is not None:
            _finish_match(state, winner, draw=False, decided_by="penalties")
            new_events.append(MatchEnded(winner, draw=False, decided_by="penalties"))

        return new_events

    handlers = {
        GoalScoredEvent: handle_goal,
        FoulCommittedEvent: handle_foul,
        EndPeriodEvent: handle_end_period,
        PenaltyKickEvent: handle_penalty_kick,
    }


def _resolve_after_regulation(
    state: FootballContestState, new_events: list[ContestEvent]
) -> list[ContestEvent]:
    if not state.is_draw or state.allow_draw:
        winner = state.leading_team()
        _finish_match(state, winner, draw=winner is None, decided_by="regulation")
        new_events.append(
            MatchEnded(winner, draw=winner is None, decided_by="regulation")
        )
        return new_events

    if state.extra_time_halves > 0:
        state.phase = MatchPhase.EXTRA_TIME
        state.start_period(PeriodKind.EXTRA_TIME)
        new_events.append(ExtraTimeStarted())
        return new_events

    state.phase = MatchPhase.PENALTIES
    new_events.append(PenaltyShootoutStarted())
    return new_events


def _resolve_after_extra_time(
    state: FootballContestState, new_events: list[ContestEvent]
) -> list[ContestEvent]:
    if not state.is_draw:
        winner = state.leading_team()
        _finish_match(state, winner, draw=False, decided_by="extra_time")
        new_events.append(MatchEnded(winner, draw=False, decided_by="extra_time"))
        return new_events

    state.phase = MatchPhase.PENALTIES
    new_events.append(PenaltyShootoutStarted())
    return new_events


def _finish_match(
    state: FootballContestState,
    winner: Optional[Contestant],
    draw: bool,
    decided_by: str,
) -> None:
    state.winner = winner
    state.was_draw = draw
    state.decided_by = decided_by
    state.phase = MatchPhase.COMPLETED
    state.is_completed = True
