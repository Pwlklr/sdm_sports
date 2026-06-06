from typing import Any
from src.core.observer import Observer
from src.core.contest import Contest
from src.sports.darts.state import DartsContestState

class DartsConsoleView(Observer):
    """
    Observer Pattern: Reacts to state changes in the match and renders
    the scoreboard to the console.
    """
    def update(self, subject: Any) -> None:
        # Safely ensure we are observing a Darts match
        if not isinstance(subject, Contest):
            return
            
        state = subject.current_state
        if not isinstance(state, DartsContestState):
            return
            
        print("\n" + "=" * 45)
        print(" 🎯 DARTS SCOREBOARD ".center(45, "="))
        
        for p in state.players:
            # Highlight current player
            marker = ">>" if state.current_player == p and not state.is_finished else "  "
            score = state.scores[p.id]
            legs = state.legs_won[p.id]
            sets = state.sets_won[p.id]
            
            print(f"{marker} {p.name:<15} | Score: {score:>3} | Legs: {legs} | Sets: {sets}")
            
        print("-" * 45)
        
        if state.is_finished:
            print("🏆 MATCH CONCLUDED 🏆".center(45))
        elif state.current_turn:
            dart_num = len(state.current_turn.throws) + 1
            print(f"Turn: {state.current_player.name} (Dart {dart_num} of 3)")
            
        print("=" * 45)