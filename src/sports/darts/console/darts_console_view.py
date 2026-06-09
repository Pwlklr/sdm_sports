from typing import Any, Optional

from src.core.contest import Contest
from src.core.contest.event import Event
from src.core.contest.observer import Observer
from src.sports.darts.contest.darts_contest_state import DartsContestState


class DartsConsoleView(Observer):
    def update(self, subject: Any, fact: Optional[Event] = None) -> None:
        if not isinstance(subject, Contest):
            return

        state = subject.current_state
        if not isinstance(state, DartsContestState):
            return

        print("\n" + "=" * 45)
        print(" 🎯 DARTS SCOREBOARD ".center(45, "="))

        for p in state.players:
            marker = (
                ">>" if state.current_player == p and not state.is_completed else "  "
            )
            score = state.scores[p.id]
            legs = state.legs_won[p.id]
            sets = state.sets_won[p.id]

            print(
                f"{marker} {p.name:<15} | Score: {score:>3} | Legs: {legs} | Sets: {sets}"
            )

        print("-" * 45)

        if state.is_completed:
            print("🏆 MATCH CONCLUDED 🏆".center(45))
        elif state.current_turn:
            throws_in_turn = len(state.current_turn.throws)
            if throws_in_turn < state.darts_per_turn:
                print(
                    f"Turn: {state.current_player.name} "
                    f"(Dart {throws_in_turn + 1} of {state.darts_per_turn})"
                )

        print("=" * 45)
