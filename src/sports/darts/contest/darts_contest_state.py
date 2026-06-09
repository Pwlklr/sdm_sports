from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar, Dict, List, Optional

from src.core.contest.event import Event
from src.core.contest.contest_state import ContestState
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

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.sports.darts.contest.darts_match_config import DartsMatchConfig


class DartsContestState(ContestState):
    _appliers: ClassVar[
        dict[type[Event], Callable[["DartsContestState", Event], None]]
    ] = {}

    def __init__(
        self,
        players: List[Contestant],
        config: Optional[DartsMatchConfig] = None,
        starting_score: int = 501,
        sets_to_win: int = 3,
        legs_to_win_set: int = 3,
    ) -> None:
        super().__init__()
        if not players:
            raise ValueError("A match requires at least one contestant.")

        self.players = players
        self.config = config

        if config:
            self.starting_score = config.starting_score
            self.sets_to_win = config.sets_to_win_match
            self.legs_to_win_set = config.legs_to_win_set
            self.in_multiplier = config.in_multiplier
            self.out_multiplier = config.out_multiplier
            self.darts_per_turn = config.darts_per_turn
        else:
            self.starting_score = starting_score
            self.sets_to_win = sets_to_win
            self.legs_to_win_set = legs_to_win_set
            self.in_multiplier = 1
            self.out_multiplier = 2
            self.darts_per_turn = 3

        self.scores: Dict[str, int] = {p.id: self.starting_score for p in players}
        self.legs_won: Dict[str, int] = {p.id: 0 for p in players}
        self.sets_won: Dict[str, int] = {p.id: 0 for p in players}

        self.leg_starting_player_idx: int = 0
        self.current_player_idx: int = 0
        self.current_turn: Optional[DartTurn] = None
        self.turn_starting_score: int = self.starting_score
        self.match_started: bool = False
        self.is_completed: bool = False
        self.winner_id: Optional[str] = None

    @property
    def current_player(self) -> Contestant:
        return self.players[self.current_player_idx]

    def player_by_id(self, player_id: str) -> Optional[Contestant]:
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def _ensure_turn(self) -> None:
        if self.current_turn is None:
            self.current_turn = DartTurn()
            self.turn_starting_score = self.scores[self.current_player.id]

    def _start_new_turn(self) -> None:
        self.current_turn = DartTurn()
        self.turn_starting_score = self.scores[self.current_player.id]

    def _advance_player(self) -> None:
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def apply(self, fact: Event) -> None:
        handler = self._appliers.get(type(fact))
        if handler:
            handler(self, fact)


def _apply_match_started(state: DartsContestState, fact: Event) -> None:
    state.match_started = True
    state._start_new_turn()


def _apply_dart_scored(state: DartsContestState, fact: Event) -> None:
    assert isinstance(fact, DartScored)
    state._ensure_turn()
    assert state.current_turn is not None
    state.current_turn.add_throw(DartThrow(fact.sector, fact.multiplier))
    state.scores[fact.player_id] -= fact.points


def _apply_busted(state: DartsContestState, fact: Event) -> None:
    assert isinstance(fact, Busted)
    state.scores[fact.player_id] = state.turn_starting_score


def _apply_turn_ended(state: DartsContestState, fact: Event) -> None:
    state._advance_player()
    state._start_new_turn()


def _apply_leg_won(state: DartsContestState, fact: Event) -> None:
    assert isinstance(fact, LegWon)
    state.legs_won[fact.player_id] += 1


def _apply_set_won(state: DartsContestState, fact: Event) -> None:
    assert isinstance(fact, SetWon)
    state.sets_won[fact.player_id] += 1
    for player in state.players:
        state.legs_won[player.id] = 0


def _apply_leg_started(state: DartsContestState, fact: Event) -> None:
    assert isinstance(fact, LegStarted)
    for player in state.players:
        state.scores[player.id] = state.starting_score
    for idx, player in enumerate(state.players):
        if player.id == fact.starting_player_id:
            state.leg_starting_player_idx = idx
            state.current_player_idx = idx
            break
    state._start_new_turn()


def _apply_match_concluded(state: DartsContestState, fact: Event) -> None:
    assert isinstance(fact, MatchConcluded)
    state.winner_id = fact.winner_id
    state.is_completed = True


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
