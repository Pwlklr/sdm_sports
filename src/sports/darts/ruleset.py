from typing import ClassVar, cast
from src.core.ruleset import RuleSet, Handler
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.sports.darts.state import DartsContestState
from src.sports.darts.events import (
    DartThrownEvent, ScoreBustedEvent, LegWonEvent, SetWonEvent, MatchEndedEvent
)

class DartsRuleSet(RuleSet):
    def _handle_dart_thrown(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        dart_event = cast(DartThrownEvent, event)
        darts_state = cast(DartsContestState, state)
        resulting_events: list[ContestEvent] = []
        
        if darts_state.is_completed:
            return resulting_events 

        player_id = dart_event.player_id
        current_score = darts_state.current_scores.get(player_id)
        if current_score is None:
            return resulting_events 

        points_scored = dart_event.points
        new_score = current_score - points_scored
        darts_state.darts_thrown_this_turn += 1

        # Rule 1: Bust Logic
        if new_score < 0 or new_score == 1 or (new_score == 0 and dart_event.multiplier != 2):
            # Domain Requirement: Revert score to what it was at the start of the turn
            darts_state.current_scores[player_id] = darts_state.turn_start_scores[player_id]
            darts_state.last_action_message = f"💥 BUST! {points_scored} scored, but busted. Turn passes."
            resulting_events.append(ScoreBustedEvent(player_id=player_id, reason="Bust condition met."))
            darts_state.switch_turn()
        
        # Rule 2: Winning Logic
        elif new_score == 0 and dart_event.multiplier == 2:
            darts_state.update_score(player_id, points_scored)
            darts_state.last_action_message = f"🎯 LEG WON by {darts_state.active_player.name}!"
            resulting_events.append(LegWonEvent(player_id=player_id))
            darts_state.legs_won[player_id] += 1
            
            if darts_state.legs_won[player_id] >= darts_state.config.legs_to_win_set:
                resulting_events.append(SetWonEvent(player_id=player_id))
                darts_state.sets_won[player_id] += 1
                darts_state.last_action_message = f"🏆 SET WON by {darts_state.active_player.name}!"
                
                if darts_state.sets_won[player_id] >= darts_state.config.sets_to_win_match:
                    darts_state.is_completed = True
                    darts_state.winner_id = player_id
                    darts_state.last_action_message = f"🎉 MATCH WON by {darts_state.active_player.name}! 🎉"
                    resulting_events.append(MatchEndedEvent(winner_id=player_id))
                else:
                    darts_state.reset_for_new_set()
            else:
                darts_state.reset_for_new_leg()
        
        # Rule 3: Valid Standard Throw
        else:
            darts_state.update_score(player_id, points_scored)
            darts_state.last_action_message = f"Good dart! Scored {points_scored}. Remaining: {new_score}"
            
            # Switch turn if 3 darts have been thrown
            if darts_state.darts_thrown_this_turn == 3:
                darts_state.last_action_message += " | Turn Over."
                darts_state.switch_turn()

        return resulting_events

    handlers: ClassVar[dict[type[ContestEvent], Handler]] = {
        DartThrownEvent: cast(Handler, _handle_dart_thrown)
    }