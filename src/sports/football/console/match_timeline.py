from __future__ import annotations

from src.core.contest import Contest
from src.core.contest.event import EventReversed
from src.sports.football.contest.events import (
    GoalScored,
    MatchConcluded,
    PenaltyKickTaken,
    PenaltyShootoutStarted,
    PeriodEnded,
    PeriodStarted,
    PlayerCautioned,
    PlayerDismissed,
    PlayerSubstituted,
)
from src.sports.football.contest.roster import player_name_for_id
from src.sports.football.contest.football_contest_state import FootballContestState


def reversed_event_ids(contest: Contest) -> set[str]:
    return {
        event.target_event_id
        for event in contest.history
        if isinstance(event, EventReversed)
    }


def active_goals(contest: Contest) -> list[tuple[int, GoalScored]]:
    """Non-reversed goals in chronological order, numbered from 1 (for VAR selection)."""
    disallowed = reversed_event_ids(contest)
    goals = [
        event
        for event in contest.history
        if isinstance(event, GoalScored) and event.event_id not in disallowed
    ]
    return list(enumerate(goals, start=1))


def _team_name(state: FootballContestState, team_id: str) -> str:
    team = state.team_by_id(team_id)
    return team.name if team is not None else "?"


def build_match_timeline(contest: Contest) -> list[str]:
    """Full chronological match log folded from the event history."""
    state = contest.current_state
    if not isinstance(state, FootballContestState):
        return []

    disallowed = reversed_event_ids(contest)
    lines: list[str] = []
    for event in contest.history:
        if isinstance(event, PeriodStarted):
            lines.append(f"-- {event.kind.value} (okres {event.index + 1}) rozpoczety")
        elif isinstance(event, GoalScored):
            label = (
                "samobojczy" if event.own_goal else "karny" if event.penalty else "gol"
            )
            scorer = player_name_for_id(state, event.scorer_id)
            scorer_text = f" {scorer}" if scorer else ""
            text = f"{event.minute}' GOL ({label}) {_team_name(state, event.team_id)}{scorer_text}"
            if event.event_id in disallowed:
                text = f"[ANULOWANY] {text}"
            lines.append(text)
        elif isinstance(event, PlayerCautioned):
            lines.append(
                f"{event.minute}' zolta kartka {player_name_for_id(state, event.offender_id)}"
            )
        elif isinstance(event, PlayerDismissed):
            lines.append(
                f"{event.minute}' czerwona kartka {player_name_for_id(state, event.offender_id)}"
            )
        elif isinstance(event, PlayerSubstituted):
            out_name = player_name_for_id(state, event.player_out)
            in_name = player_name_for_id(state, event.player_in)
            lines.append(f"{event.minute}' zmiana: {out_name} -> {in_name}")
        elif isinstance(event, PeriodEnded):
            lines.append(f"-- koniec okresu ({event.kind.value})")
        elif isinstance(event, PenaltyShootoutStarted):
            lines.append("-- seria rzutow karnych")
        elif isinstance(event, PenaltyKickTaken):
            outcome = "trafiony" if event.scored else "obroniony/niecelny"
            lines.append(f"   karny {_team_name(state, event.team_id)}: {outcome}")
        elif isinstance(event, MatchConcluded):
            via = event.decided_by.replace("_", " ")
            lines.append(f"== koniec meczu ({via})")
        elif isinstance(event, EventReversed):
            lines.append(f"   (VAR) wycofano zdarzenie - powod: {event.reason}")
    return lines


def print_match_timeline(contest: Contest) -> None:
    lines = build_match_timeline(contest)
    print("\n--- PRZEBIEG MECZU ---")
    if not lines:
        print("  (brak zdarzen)")
    for line in lines:
        print(f"  {line}")
    print("----------------------")
