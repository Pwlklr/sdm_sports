from __future__ import annotations
from typing import TYPE_CHECKING, Any

from src.core.ruleset import RuleSet
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.sports.darts.events import (
    DartThrownEvent, ScoreBusted, TurnEnded, LegWon, SetWon, MatchEnded
)
from src.sports.darts.state import DartsContestState
from src.sports.darts.disciplinary import BustViolation, BustPenalty


class DartsRuleSet(RuleSet):
    """
    Evaluates Darts events against the current state, enforcing rules
    like Busts, Double-Out wins, and Turn limits. Returns cascading events.
    """

    # We type 'self' as the base RuleSet to perfectly match the base class signature,
    # then assert it to DartsRuleSet inside the method.
    def handle_dart_thrown(self: RuleSet, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        assert isinstance(event, DartThrownEvent)
        assert isinstance(state, DartsContestState)

        new_events: list[ContestEvent] = []

        if state.is_finished:
            return new_events

        # Ensure a turn is active
        if state.current_turn is None:
            state.start_new_turn()

        # Tell MyPy that current_turn is definitively not None
        current_turn = state.current_turn
        assert current_turn is not None

        player_id = state.current_player.id
        player = state.current_player

        # 1. Add the throw to the aggregate
        current_turn.add_throw(event.dart_throw)

        # 2. Calculate projected score
        projected_score = state.turn_starting_score - current_turn.total_points

        # 3. Rule: Bust Check
        is_bust = False
        if projected_score < 0 or projected_score == 1:
            is_bust = True
        elif projected_score == 0 and event.dart_throw.multiplier != 2:
            is_bust = True

        if is_bust:
            # Trigger Disciplinary Pipeline
            violation = BustViolation(player, "Score busted!")
            penalty = BustPenalty(violation)
            penalty.apply(current_turn)
            
            # Revert score and pass turn
            state.scores[player_id] = state.turn_starting_score
            state.advance_player()
            state.start_new_turn()
            
            # Cascade Events
            new_events.append(ScoreBusted(player))
            new_events.append(TurnEnded(player))
            return new_events

        # 4. Normal Throw: Update temporary score
        state.scores[player_id] = projected_score

        # 5. Rule: Win Leg Check
        if projected_score == 0 and event.dart_throw.multiplier == 2:
            state.legs_won[player_id] += 1
            new_events.append(LegWon(player))
            
            # Check Set Win
            if state.legs_won[player_id] >= state.legs_to_win_set:
                state.sets_won[player_id] += 1
                new_events.append(SetWon(player))
                
                # Reset legs for new set
                for p in state.players:
                    state.legs_won[p.id] = 0
                
                # Check Match Win
                if state.sets_won[player_id] >= state.sets_to_win:
                    state.is_finished = True
                    new_events.append(MatchEnded(player))
                    return new_events

            # Leg or Set won (but match not over), reset for next leg
            state.reset_for_new_leg()
            state.start_new_turn()
            return new_events

        # 6. Rule: Natural Turn End (3 darts thrown)
        if current_turn.is_finished:
            state.advance_player()
            state.start_new_turn()
            new_events.append(TurnEnded(player))

        return new_events

    # By omitting the explicit 'dict[...]' annotation here, we inherit the ClassVar 
    # constraint from the base class seamlessly without triggering MyPy overriding errors.
    handlers = {
        DartThrownEvent: handle_dart_thrown
    }

    def evaluate(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        """Dispatches the event to the appropriate handler and returns cascading events."""
        handler = self.handlers.get(type(event))
        if handler:
            return handler(self, event, state)
        return []