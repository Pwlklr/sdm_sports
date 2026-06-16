from typing import Any, Optional

from src.core.contest import Contest
from src.core.contest.event import Event
from src.core.contest.observer import Observer
from src.core.contestant.models import Team
from src.sports.football.contest.roster import player_name_for_id
from src.sports.football.contest.roster_status import team_disciplinary_summary
from src.sports.football.console.roster_view import (
    format_pitch_and_bench_lines_from_state,
    format_team_header,
)
from src.sports.football.contest.football_contest_state import (
    FootballContestState,
    MatchPhase,
)


class FootballConsoleView(Observer):
    def update(self, subject: Any, fact: Optional[Event] = None) -> None:
        if not isinstance(subject, Contest):
            return

        state = subject.current_state
        if not isinstance(state, FootballContestState):
            return

        print("\n" + "=" * 45)
        print(" ⚽ FOOTBALL SCOREBOARD ".center(45, "="))

        for team_number, team in enumerate(state.teams, start=1):
            if not isinstance(team, Team):
                continue
            goals = state.scores[team.id]
            yellows, sent_off = team_disciplinary_summary(team, state)
            card_info = ""
            if yellows:
                card_info += f" | 🟨 {yellows}"
            if sent_off:
                card_info += f" | 🟥 {sent_off}"
            print(
                f"   {format_team_header(team_number, team):<28} | Goals: {goals:>2}{card_info}"
            )

        print("-" * 45)
        print("Squads (team # + player # from 1; cards shown per player):")
        for team_number, team in enumerate(state.teams, start=1):
            if not isinstance(team, Team):
                continue
            print(f"  Team {team_number}: {team.name}")
            for line in format_pitch_and_bench_lines_from_state(state, team):
                print(line)

        print("-" * 45)

        if state.is_finished:
            if state.was_draw:
                print("🤝 FULL TIME — DRAW 🤝".center(45))
            elif state.winner is not None:
                try:
                    via = subject.get_official_result().decided_by.replace("_", " ")
                except Exception:
                    via = "regulation"
                print(f"🏆 {state.winner.name} WIN ({via}) 🏆".center(45))
        elif state.phase == MatchPhase.PENALTIES:
            print("PENALTY SHOOTOUT".center(45))
            for team_number, t in enumerate(state.teams, start=1):
                print(
                    f"   {team_number}={t.name:<18} | "
                    f"{state.penalty_scores[t.id]}/{state.penalty_attempts[t.id]}"
                )
        else:
            period = state.current_period
            if period is not None:
                print(f"In progress: {period.kind.value} (Period {period.index + 1})")
                for goal in period.goals:
                    label = "OG" if goal.own_goal else "PEN" if goal.penalty else "G"
                    scorer = player_name_for_id(state, goal.scorer_id)
                    scorer_text = f" {scorer}" if scorer else ""
                    print(f"   {goal.minute}' {label}{scorer_text}")

        print("=" * 45)
