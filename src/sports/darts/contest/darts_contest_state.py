from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import ClassVar, Optional

from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event
from src.core.contestant.models import Contestant, IndividualPlayer
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.entities import DartThrow, DartTurn
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
from src.sports.darts.contest.player_stats import DartsPlayerStats


@dataclass(frozen=True, kw_only=True)
class DartsContestState(ContestState):
    players: tuple[IndividualPlayer, ...]
    config: DartsMatchConfig
    scores: dict[str, int] = field(default_factory=dict)
    contestant_stats: dict[str, DartsPlayerStats] = field(default_factory=dict)
    leg_starting_player_idx: int = 0
    current_player_idx: int = 0
    current_turn: Optional[DartTurn] = None
    turn_starting_score: int = 0
    match_started: bool = False
    is_finished: bool = False
    winner_id: Optional[str] = None

    _appliers: ClassVar[
        dict[type[Event], Callable[["DartsContestState", Event], DartsContestState]]
    ] = {}

    def __post_init__(self) -> None:
        if not self.players:
            raise ValueError("A match requires at least one contestant.")
        for player in self.players:
            if not isinstance(player, IndividualPlayer):
                raise ValueError("Darts matches require IndividualPlayer contestants.")

    @property
    def contestants(self) -> list[Contestant]:
        return list(self.players)

    @property
    def current_player(self) -> Contestant:
        return self.players[self.current_player_idx]

    @property
    def legs_won(self) -> dict[str, int]:
        return {pid: s.legs_won for pid, s in self.contestant_stats.items()}

    @property
    def sets_won(self) -> dict[str, int]:
        return {pid: s.sets_won for pid, s in self.contestant_stats.items()}

    def player_by_id(self, player_id: str) -> Optional[Contestant]:
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def apply(self, fact: Event) -> DartsContestState:
        handler = self._appliers.get(type(fact))
        if handler:
            return handler(self, fact)
        return self

    def reset(self) -> DartsContestState:
        return create_darts_contest_state(list(self.players), self.config)


def _start_new_turn(state: DartsContestState) -> DartsContestState:
    return replace(
        state,
        current_turn=DartTurn(),
        turn_starting_score=state.scores[state.current_player.id],
    )


def _ensure_turn(state: DartsContestState) -> DartsContestState:
    if state.current_turn is None:
        return _start_new_turn(state)
    return state


def _advance_player(state: DartsContestState) -> DartsContestState:
    idx = (state.current_player_idx + 1) % len(state.players)
    return replace(state, current_player_idx=idx)


def _apply_match_started(state: DartsContestState, fact: Event) -> DartsContestState:
    return _start_new_turn(replace(state, match_started=True))


def _apply_dart_scored(state: DartsContestState, fact: Event) -> DartsContestState:
    assert isinstance(fact, DartScored)
    state = _ensure_turn(state)
    assert state.current_turn is not None
    turn = state.current_turn.with_throw(
        DartThrow(sector=fact.sector, multiplier=fact.multiplier)
    )
    scores = dict(state.scores)
    scores[fact.player_id] = scores.get(fact.player_id, 0) - fact.points
    stats = dict(state.contestant_stats)
    if fact.player_id in stats:
        stats[fact.player_id] = stats[fact.player_id].with_dart_thrown(fact.points)
    return replace(state, current_turn=turn, scores=scores, contestant_stats=stats)


def _apply_busted(state: DartsContestState, fact: Event) -> DartsContestState:
    assert isinstance(fact, Busted)
    scores = dict(state.scores)
    scores[fact.player_id] = state.turn_starting_score
    return replace(state, scores=scores)


def _apply_turn_ended(state: DartsContestState, fact: Event) -> DartsContestState:
    state = _advance_player(state)
    return _start_new_turn(state)


def _apply_leg_won(state: DartsContestState, fact: Event) -> DartsContestState:
    assert isinstance(fact, LegWon)
    stats = dict(state.contestant_stats)
    if fact.player_id in stats:
        stats[fact.player_id] = stats[fact.player_id].with_leg_won()
    return replace(state, contestant_stats=stats)


def _apply_set_won(state: DartsContestState, fact: Event) -> DartsContestState:
    assert isinstance(fact, SetWon)
    stats = dict(state.contestant_stats)
    if fact.player_id in stats:
        stats[fact.player_id] = stats[fact.player_id].with_set_won()
    for player in state.players:
        if player.id in stats:
            s = stats[player.id]
            stats[player.id] = DartsPlayerStats(
                contestant_id=s.contestant_id,
                sets_won=s.sets_won,
                legs_won=0,
                darts_thrown=s.darts_thrown,
                highest_checkout=s.highest_checkout,
            )
    return replace(state, contestant_stats=stats)


def _apply_leg_started(state: DartsContestState, fact: Event) -> DartsContestState:
    assert isinstance(fact, LegStarted)
    scores = {player.id: state.config.starting_score for player in state.players}
    current_idx = state.current_player_idx
    leg_idx = state.leg_starting_player_idx
    for idx, player in enumerate(state.players):
        if player.id == fact.starting_player_id:
            leg_idx = idx
            current_idx = idx
            break
    state = replace(
        state,
        scores=scores,
        leg_starting_player_idx=leg_idx,
        current_player_idx=current_idx,
    )
    return _start_new_turn(state)


def _apply_match_concluded(state: DartsContestState, fact: Event) -> DartsContestState:
    assert isinstance(fact, MatchConcluded)
    return replace(
        state,
        winner_id=fact.winner_id,
        is_finished=True,
    )


DartsContestState._appliers = {
    MatchStarted: _apply_match_started,
    DartScored: _apply_dart_scored,
    Busted: _apply_busted,
    TurnEnded: _apply_turn_ended,
    LegWon: _apply_leg_won,
    SetWon: _apply_set_won,
    LegStarted: _apply_leg_started,
    MatchConcluded: _apply_match_concluded,
}


def _require_individual_player(player: Contestant) -> IndividualPlayer:
    if not isinstance(player, IndividualPlayer):
        raise ValueError("Darts matches require IndividualPlayer contestants.")
    return player


def create_darts_contest_state(
    players: list[Contestant],
    config: DartsMatchConfig,
) -> DartsContestState:
    if not players:
        raise ValueError("A match requires at least one contestant.")
    typed: tuple[IndividualPlayer, ...] = tuple(
        _require_individual_player(player) for player in players
    )
    return DartsContestState(
        players=typed,
        config=config,
        scores={p.id: config.starting_score for p in typed},
        contestant_stats={p.id: DartsPlayerStats(contestant_id=p.id) for p in typed},
        turn_starting_score=config.starting_score,
    )
