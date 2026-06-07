from __future__ import annotations
from typing import TYPE_CHECKING, Any

from src.core.ruleset import RuleSet
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.sports.darts.events import (
    DartThrownEvent, ScoreBusted, TurnEnded, LegWon, SetWon, MatchEnded, OcheFaultEvent
)
from src.sports.darts.state import DartsContestState
from src.sports.darts.disciplinary import (
    BustViolation, BustPenalty, OcheFaultViolation, InvalidThrowPenalty
)
from src.sports.darts.entities import DartThrow

class DartsRuleSet(RuleSet):
    """
    Evaluates Darts events against the current state, enforcing rules
    like Busts, Double-Out wins, and Turn limits.
    """

    def handle_oche_fault(self: RuleSet, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        assert isinstance(event, OcheFaultEvent)
        assert isinstance(state, DartsContestState)

        new_events: list[ContestEvent] = []

        if state.is_completed:
            return new_events

        if state.current_turn is None:
            state.start_new_turn()
            
        current_turn = state.current_turn
        assert current_turn is not None

        # 1. Trigger Disciplinary Pipeline
        violation = OcheFaultViolation(event.player)
        penalty = InvalidThrowPenalty(violation)
        penalty.apply(current_turn)
        
        # 2. An Oche Fault costs the player 1 dart, but scores 0 points
        fault_throw = DartThrow(0, 1)
        current_turn.add_throw(fault_throw)

        # 3. Rule: Natural Turn End (3 darts thrown)
        if current_turn.is_finished:
            state.advance_player()
            state.start_new_turn()
            new_events.append(TurnEnded(event.player))

        return new_events

    def handle_dart_thrown(self: RuleSet, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        assert isinstance(event, DartThrownEvent)
        assert isinstance(state, DartsContestState)

        new_events: list[ContestEvent] = []

        if state.is_completed:
            return new_events

        if state.current_turn is None:
            state.start_new_turn()

        current_turn = state.current_turn
        assert current_turn is not None

        player_id = state.current_player.id
        player = state.current_player

        current_turn.add_throw(event.dart_throw)
        projected_score = state.turn_starting_score - current_turn.total_points

        # Bust Check
        is_bust = False
        if projected_score < 0 or projected_score == 1:
            is_bust = True
        elif projected_score == 0 and event.dart_throw.multiplier != 2:
            is_bust = True

        if is_bust:
            violation = BustViolation(player, "Score busted!")
            penalty = BustPenalty(violation)
            penalty.apply(current_turn)
            
            state.scores[player_id] = state.turn_starting_score
            state.advance_player()
            state.start_new_turn()
            
            new_events.append(ScoreBusted(player))
            new_events.append(TurnEnded(player))
            return new_events

        state.scores[player_id] = projected_score

        # Win Leg Check
        if projected_score == 0 and event.dart_throw.multiplier == 2:
            state.legs_won[player_id] += 1
            new_events.append(LegWon(player))
            
            if state.legs_won[player_id] >= state.legs_to_win_set:
                state.sets_won[player_id] += 1
                new_events.append(SetWon(player))
                
                for p in state.players:
                    state.legs_won[p.id] = 0
                
                if state.sets_won[player_id] >= state.sets_to_win:
                    state.is_completed = True
                    new_events.append(MatchEnded(player))
                    return new_events

            state.reset_for_new_leg()
            state.start_new_turn()
            return new_events

        # Natural Turn End Check
        if current_turn.is_finished:
            state.advance_player()
            state.start_new_turn()
            new_events.append(TurnEnded(player))

        return new_events

    handlers = {
        DartThrownEvent: handle_dart_thrown,
        OcheFaultEvent: handle_oche_fault
    }

    def evaluate(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        handler = self.handlers.get(type(event))
        if handler:
            return handler(self, event, state)
        return []