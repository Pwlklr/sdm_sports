from __future__ import annotations

from src.core.contest import Contest
from src.core.contest.command import ReverseDecision
from src.core.console.reversal_catalog import ReversalOption, build_numbered_catalog
from src.core.contest.event import Event
from src.sports.football.contest.commands import RevokeCaution, VarOverturnGoal
from src.sports.football.contest.events import (
    GoalScored,
    PenaltyKickTaken,
    PlayerCautioned,
    PlayerDismissed,
    PlayerSubstituted,
)
from src.sports.football.contest.roster import player_name_for_id
from src.sports.football.contest.state import FootballContestState

_REVERSIBLE_TYPES = (
    GoalScored,
    PlayerCautioned,
    PlayerDismissed,
    PlayerSubstituted,
    PenaltyKickTaken,
)


def _team_name(state: FootballContestState, team_id: str) -> str:
    team = state.team_by_id(team_id)
    return team.name if team is not None else "?"


def _label_event(state: FootballContestState, event: Event) -> str:
    if isinstance(event, GoalScored):
        kind = "samoboj" if event.own_goal else "karny" if event.penalty else "gol"
        scorer = player_name_for_id(state, event.scorer_id)
        scorer_text = f" {scorer}" if scorer else ""
        return (
            f"{event.minute}' {kind} {_team_name(state, event.team_id)}{scorer_text}"
        )
    if isinstance(event, PlayerCautioned):
        return (
            f"{event.minute}' zolta kartka "
            f"{player_name_for_id(state, event.offender_id)}"
        )
    if isinstance(event, PlayerDismissed):
        return (
            f"{event.minute}' czerwona kartka "
            f"{player_name_for_id(state, event.offender_id)}"
        )
    if isinstance(event, PlayerSubstituted):
        out_name = player_name_for_id(state, event.player_out)
        in_name = player_name_for_id(state, event.player_in)
        return f"{event.minute}' zmiana {out_name} -> {in_name}"
    if isinstance(event, PenaltyKickTaken):
        outcome = "trafiony" if event.scored else "pudlo"
        return f"karny seria {_team_name(state, event.team_id)}: {outcome}"
    return type(event).__name__


def build_football_reversal_catalog(
    contest: Contest,
    state: FootballContestState,
    *,
    goals_only: bool = False,
) -> list[ReversalOption]:
    events = [
        event
        for event in contest.active_domain_events()
        if isinstance(event, _REVERSIBLE_TYPES)
    ]
    if goals_only:
        events = [event for event in events if isinstance(event, GoalScored)]
    return build_numbered_catalog(events, lambda event: _label_event(state, event))


def football_reverse_command(
    contest: Contest,
    event_id: str,
    *,
    reason: str,
) -> ReverseDecision:
    event = next(e for e in contest.history if e.event_id == event_id)
    if isinstance(event, GoalScored):
        return VarOverturnGoal(target_event_id=event_id, reason=reason)
    if isinstance(event, PlayerCautioned):
        return RevokeCaution(target_event_id=event_id, reason=reason)
    return ReverseDecision(target_event_id=event_id, reason=reason)
