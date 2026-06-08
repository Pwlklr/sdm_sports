from typing import Any

from src.core.contest import Contest
from src.core.observer import Observer
from src.sports.football.state import FootballContestState, MatchPhase


class FootballConsoleView(Observer):
    def update(self, subject: Any) -> None:
        if not isinstance(subject, Contest):
            return

        state = subject.current_state
        if not isinstance(state, FootballContestState):
            return

        print("\n" + "=" * 45)
        print(" ⚽ FOOTBALL SCOREBOARD ".center(45, "="))

        for t in state.teams:
            goals = state.scores[t.id]
            cautions = state.disciplinary.yellow_cards.get(t.id, 0)
            sent_off = "🟥" if state.disciplinary.is_dismissed(t.id) else ""
            card_info = ""
            if cautions:
                card_info += f" | 🟨 {cautions}"
            if sent_off:
                card_info += f" | {sent_off}"
            print(f"   {t.name:<20} | Goals: {goals:>2}{card_info}")

        print("-" * 45)

        if state.is_completed:
            if state.was_draw:
                print("🤝 FULL TIME — DRAW 🤝".center(45))
            elif state.winner is not None:
                via = state.decided_by.replace("_", " ")
                print(f"🏆 {state.winner.name} WIN ({via}) 🏆".center(45))
        elif state.phase == MatchPhase.PENALTIES:
            print("PENALTY SHOOTOUT".center(45))
            for t in state.teams:
                print(
                    f"   {t.name:<20} | "
                    f"{state.penalty_scores[t.id]}/{state.penalty_attempts[t.id]}"
                )
        else:
            period = state.current_period
            if period is not None:
                print(f"In progress: {period.kind.value} (Period {period.index + 1})")

        print("=" * 45)
