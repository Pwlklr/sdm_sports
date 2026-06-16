from __future__ import annotations

from typing import ClassVar

from src.core.contest.command import Command
from src.core.contest.event import Event
from src.core.contest.rule_set import Handler, RuleSet
from src.core.shared.command_rejected import reject
from src.sports.darts.contest.commands import (
    AwardWalkover,
    CallOcheFault,
    StartMatch,
    ThrowDart,
)
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.events import (
    Busted,
    ContestResultOverridden,
    DartScored,
    LegStarted,
    LegWon,
    MatchConcluded,
    MatchStarted,
    SetWon,
    TurnEnded,
)


def _dart_points(sector: int, multiplier: int) -> int:
    return sector * multiplier


class DartsCoreRules:
    def decide_start_match(
        self, command: StartMatch, state: DartsContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest juz zakonczony.")
        if state.match_started:
            reject("Mecz zostal juz rozpoczety.")
        return [MatchStarted()]

    def decide_throw_dart(
        self, command: ThrowDart, state: DartsContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna rzucac.")

        if state.current_turn is None:
            reject("Brak aktywnej tury - rozpocznij mecz.")

        if len(state.current_turn.throws) >= state.config.darts_per_turn:
            reject("Tura jest juz zakonczona (limit lotek osiagniety).")

        player_id = state.current_player.id
        pts_scored = _dart_points(command.sector, command.multiplier)
        if state.scores[player_id] == state.config.starting_score:
            if (
                state.config.in_multiplier > 1
                and command.multiplier != state.config.in_multiplier
            ):
                pts_scored = 0

        projected_score = state.scores[player_id] - pts_scored

        if _is_bust(projected_score, command.sector, command.multiplier, state):
            return [Busted(player_id=player_id)]

        return [
            DartScored(
                player_id=player_id,
                sector=command.sector,
                multiplier=command.multiplier,
                points=pts_scored,
            )
        ]

    def decide_oche_fault(
        self, command: CallOcheFault, state: DartsContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna zglosic faulu.")
        if state.current_turn is None:
            reject("Brak aktywnej tury - rozpocznij mecz.")
        if len(state.current_turn.throws) >= state.config.darts_per_turn:
            reject("Tura jest juz zakonczona (limit lotek osiagniety).")

        return [
            DartScored(
                player_id=state.current_player.id,
                sector=0,
                multiplier=1,
                points=0,
            )
        ]

    def react_dart_scored(
        self, fact: DartScored, state: DartsContestState
    ) -> list[Event]:
        if state.scores[fact.player_id] == 0:
            return [LegWon(player_id=fact.player_id)]

        turn = state.current_turn
        if turn is not None and len(turn.throws) >= state.config.darts_per_turn:
            return [TurnEnded(player_id=fact.player_id)]
        return []

    def react_busted(self, fact: Busted, state: DartsContestState) -> list[Event]:
        return [TurnEnded(player_id=fact.player_id)]

    def react_leg_won(self, fact: LegWon, state: DartsContestState) -> list[Event]:
        if state.legs_won[fact.player_id] >= state.config.legs_to_win_set:
            return [SetWon(player_id=fact.player_id)]

        next_starter_idx = (state.leg_starting_player_idx + 1) % len(state.players)
        return [LegStarted(starting_player_id=state.players[next_starter_idx].id)]

    def react_set_won(self, fact: SetWon, state: DartsContestState) -> list[Event]:
        if state.sets_won[fact.player_id] >= state.config.sets_to_win_match:
            return [MatchConcluded(winner_id=fact.player_id, decided_by="regulation")]

        next_starter_idx = (state.leg_starting_player_idx + 1) % len(state.players)
        return [LegStarted(starting_player_id=state.players[next_starter_idx].id)]

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        StartMatch: decide_start_match,
        ThrowDart: decide_throw_dart,
        CallOcheFault: decide_oche_fault,
    }

    _own_reaction_handlers: ClassVar[dict[type[Event], Handler]] = {
        DartScored: react_dart_scored,
        Busted: react_busted,
        LegWon: react_leg_won,
        SetWon: react_set_won,
    }


class DartsAdminRules:
    """Post-match administrative walkover / result override."""

    def decide_award_walkover(
        self, command: AwardWalkover, state: DartsContestState, history: list[Event]
    ) -> list[Event]:
        if state.player_by_id(command.winner_id) is None:
            reject("Nieprawidlowy zwyciezca.")

        if state.match_started and not state.is_finished:
            reject("Mecz trwa - walkover administracyjny niedostepny w trakcie gry.")

        if not state.is_finished:
            return [
                MatchConcluded(
                    winner_id=command.winner_id,
                    decided_by=command.reason,
                )
            ]

        return [
            ContestResultOverridden(
                winner_id=command.winner_id,
                reason=command.reason,
            )
        ]

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        AwardWalkover: decide_award_walkover,
    }


class DartsRuleSet(DartsCoreRules, DartsAdminRules, RuleSet):
    def __init__(self, config: DartsMatchConfig, reversal_chain=None) -> None:
        super().__init__(reversal_chain=reversal_chain)
        self._config = config


def _is_bust(
    projected_score: int, sector: int, multiplier: int, state: DartsContestState
) -> bool:
    if projected_score < 0:
        return True
    if (
        projected_score == 0
        and state.config.out_multiplier > 1
        and multiplier != state.config.out_multiplier
    ):
        return True
    if (
        projected_score > 0
        and state.config.out_multiplier > 1
        and projected_score < state.config.out_multiplier
    ):
        return True
    return False
