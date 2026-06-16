from __future__ import annotations

from src.core.contest import Contest
from src.core.contest.command import ReverseDecision
from src.console.reversal_catalog import ReversalOption, build_numbered_catalog
from src.core.contest.event import Event
from src.sports.darts.contest.commands import RevokeDartThrow
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.events import Busted, DartScored

_REVERSIBLE_TYPES = (DartScored, Busted)


def _player_name(state: DartsContestState, player_id: str) -> str:
    player = state.player_by_id(player_id)
    return player.name if player is not None else "?"


def _label_event(state: DartsContestState, event: Event) -> str:
    if isinstance(event, DartScored):
        name = _player_name(state, event.player_id)
        return f"{name}: {event.sector} x{event.multiplier} = {event.points} pkt"
    if isinstance(event, Busted):
        return f"{_player_name(state, event.player_id)}: BUST"
    return type(event).__name__


def build_darts_reversal_catalog(
    contest: Contest,
    state: DartsContestState,
) -> list[ReversalOption]:
    events = [
        event
        for event in contest.active_domain_events()
        if isinstance(event, _REVERSIBLE_TYPES)
    ]
    return build_numbered_catalog(events, lambda event: _label_event(state, event))


def darts_reverse_command(event_id: str, *, reason: str = "reverse") -> ReverseDecision:
    return RevokeDartThrow(target_event_id=event_id, reason=reason)
