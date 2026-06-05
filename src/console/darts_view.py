from src.core.observer import Observer, Subject
from src.core.contest import Contest
from src.sports.darts.state import DartsContestState

class DartsScoreboardObserver(Observer):
    def update(self, subject: Subject) -> None:
        if isinstance(subject, Contest) and isinstance(subject.current_state, DartsContestState):
            state = subject.current_state
            
            print("\n" + "="*45)
            print(f"{'DARTS SCOREBOARD':^45}")
            print("="*45)
            
            for player in state.players:
                score = state.current_scores.get(player.contestant_id, 0)
                legs = state.legs_won.get(player.contestant_id, 0)
                sets = state.sets_won.get(player.contestant_id, 0)
                
                marker = ">>" if state.active_player.contestant_id == player.contestant_id else "  "
                print(f"{marker} {player.name:<15} | Score: {score:>3} | Legs: {legs} | Sets: {sets}")
                
            print("-" * 45)
            print(f"Turn: {state.active_player.name} (Dart {state.darts_thrown_this_turn + 1} of 3)")
            print(f"Status: {state.last_action_message}")
            print("="*45)
            
            # Print command help only if game is still running
            if not state.is_completed:
                print("Commands: <sector> <multiplier> (e.g., '20 3' for Treble 20) | 'q' to quit match")