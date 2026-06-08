from __future__ import annotations

from typing import Optional

from src.core.commands import MatchCommand
from src.core.contest import Contest
from src.sports.football.events import (
    EndPeriodEvent,
    FoulCommittedEvent,
    GoalScoredEvent,
    MatchStarted,
    PenaltyKickEvent,
)
from src.sports.football.state import FootballContestState


class StartFootballMatchCommand(MatchCommand):
    """Initializes the match and triggers the opening lifecycle event."""

    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, FootballContestState)

        if not state.is_completed and not state.periods:
            match.process_event(MatchStarted())


class ScoreGoalCommand(MatchCommand):
    """Translates a goal input into a domain event for the given side index."""

    def __init__(
        self,
        team_index: int,
        scorer_id: Optional[str] = None,
        minute: Optional[int] = None,
        own_goal: bool = False,
        penalty: bool = False,
    ) -> None:
        self.team_index = team_index
        self.scorer_id = scorer_id
        self.minute = minute
        self.own_goal = own_goal
        self.penalty = penalty

    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, FootballContestState)

        if state.is_completed:
            return

        team = state.teams[self.team_index]
        event = GoalScoredEvent(
            team=team,
            scorer_id=self.scorer_id,
            minute=self.minute,
            own_goal=self.own_goal,
            penalty=self.penalty,
        )
        match.process_event(event)


class CommitFoulCommand(MatchCommand):
    """Translates a referee's foul/card call into a domain event."""

    def __init__(
        self,
        team_index: int,
        card: Optional[str] = None,
        offender_id: Optional[str] = None,
        reason: str = "Foul play",
    ) -> None:
        self.team_index = team_index
        self.card = card
        self.offender_id = offender_id
        self.reason = reason

    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, FootballContestState)

        if state.is_completed:
            return

        team = state.teams[self.team_index]
        match.process_event(
            FoulCommittedEvent(
                team=team,
                card=self.card,
                offender_id=self.offender_id,
                reason=self.reason,
            )
        )


class EndPeriodCommand(MatchCommand):
    """Translates a referee's whistle into the end-of-period event."""

    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, FootballContestState)

        if state.is_completed:
            return

        match.process_event(EndPeriodEvent())


class PenaltyKickCommand(MatchCommand):
    """Translates a single shootout kick into a domain event."""

    def __init__(self, team_index: int, scored: bool) -> None:
        self.team_index = team_index
        self.scored = scored

    def execute(self, match: Contest) -> None:
        state = match.current_state
        assert isinstance(state, FootballContestState)

        if state.is_completed:
            return

        team = state.teams[self.team_index]
        match.process_event(PenaltyKickEvent(team=team, scored=self.scored))
