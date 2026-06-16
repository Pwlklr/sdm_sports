from __future__ import annotations

from src.core.contest import Contest
from src.core.contest.event import EventReversed
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.events import (
    Busted,
    DartScored,
    LegStarted,
    LegWon,
    MatchConcluded,
    MatchStarted,
    SetWon,
    TurnEnded,
)


def _player_name(state: DartsContestState, player_id: str) -> str:
    player = state.player_by_id(player_id)
    return player.name if player is not None else "?"


def build_darts_timeline(contest: Contest) -> list[str]:
    state = contest.current_state
    if not isinstance(state, DartsContestState):
        return []

    lines: list[str] = []
    for event in contest.history:
        if isinstance(event, MatchStarted):
            lines.append("-- match started")
        elif isinstance(event, DartScored):
            name = _player_name(state, event.player_id)
            lines.append(
                f"{name}: {event.sector} x{event.multiplier} = {event.points} pts"
            )
        elif isinstance(event, Busted):
            lines.append(f"{_player_name(state, event.player_id)}: BUST")
        elif isinstance(event, TurnEnded):
            lines.append(f"-- end of turn ({_player_name(state, event.player_id)})")
        elif isinstance(event, LegWon):
            lines.append(f"** leg to {_player_name(state, event.player_id)}")
        elif isinstance(event, SetWon):
            lines.append(f"*** set to {_player_name(state, event.player_id)}")
        elif isinstance(event, LegStarted):
            lines.append(
                f"-- new leg (starts {_player_name(state, event.starting_player_id)})"
            )
        elif isinstance(event, MatchConcluded):
            lines.append(
                f"== match ended (winner: {_player_name(state, event.winner_id)})"
            )
        elif isinstance(event, EventReversed):
            lines.append(f"   (event reversed - reason: {event.reason})")
    return lines


def print_darts_timeline(contest: Contest) -> None:
    lines = build_darts_timeline(contest)
    print("\n--- MATCH TIMELINE ---")
    if not lines:
        print("  (no events)")
    for line in lines:
        print(f"  {line}")
    print("----------------------")
