from typing import Optional

from src.core.contest import Contest
from src.core.contest.command import Command
from src.core.contestant.models import Team
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor
from src.sports.football.console.football_command_parser import parse_football_command
from src.sports.football.console.football_console_view import FootballConsoleView
from src.sports.football.console.match_timeline import (
    active_goals,
    print_match_timeline,
)
from src.sports.football.contest.commands import StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.roster import format_team_header, player_name_for_id
from src.sports.football.contest.state import FootballContestState, MatchPhase
from src.sports.football.descriptor import FOOTBALL_SPORT


class FootballConsoleAdapter(ConsoleAdapter):
    @property
    def descriptor(self) -> SportDescriptor:
        return FOOTBALL_SPORT

    def collect_config(self) -> FootballMatchConfig:
        print("\nConfig: 1. Domyslny (FIFA)  2. Liga  3. Puchar  4. Wlasny")
        choice = input("Choice [Default 1]: ").strip() or "1"
        if choice == "2":
            return FootballMatchConfig.league()
        if choice == "3":
            return FootballMatchConfig.cup()
        if choice != "4":
            return FootballMatchConfig.fifa()

        halves = int(input("\nNumber of halves [Default 2]: ").strip() or "2")
        length = int(input("Half length in minutes [Default 45]: ").strip() or "45")
        draw_str = input("Allow draws? (y/n) [Default y]: ").strip().lower()
        allow_draw = draw_str != "n"
        return FootballMatchConfig(
            number_of_halves=halves,
            half_length_minutes=length,
            allow_draw=allow_draw,
        )

    def attach_view(self, contest: Contest) -> None:
        contest.attach(FootballConsoleView())

    def get_input_prompt(self, contest: Contest) -> str:
        state = contest.current_state
        if isinstance(state, FootballContestState):
            sides = " ".join(
                format_team_header(n, t)
                for n, t in enumerate(state.teams, start=1)
                if isinstance(t, Team)
            )
            if state.phase == MatchPhase.PENALTIES:
                return f"Penalty [{sides}] ('pk <team> g|m', 'end')"
            return (
                f"Action [{sides}] "
                "('goal/og/pen <t> <min> [player]', "
                "'yellow/red/foul <t> <player> <min> [reason]', "
                "'lineup <t> <players...>', 'sub <t> <out> <in> [min]', "
                "'roster [team]', 'log', 'var [goal#]', 'end')"
            )
        return "Action"

    def parse_command(self, user_input: str, contest: Contest) -> Optional[Command]:
        state = contest.current_state
        if not isinstance(state, FootballContestState):
            return None

        cleaned = user_input.strip().lower()
        verb = cleaned.split()[0] if cleaned.split() else ""

        if verb == "log":
            print_match_timeline(contest)
            return None

        if verb == "var":
            self._handle_var(cleaned, contest, state)
            return None

        return parse_football_command(user_input, state)

    def _handle_var(
        self, cleaned: str, contest: Contest, state: FootballContestState
    ) -> None:
        goals = active_goals(contest)
        if not goals:
            print("❌ Brak goli do anulowania.")
            return

        parts = cleaned.split()
        if len(parts) == 1:
            print("\n--- VAR: wybierz gol do anulowania ('var <numer>') ---")
            for number, goal in goals:
                team = state.team_by_id(goal.team_id)
                team_name = team.name if team is not None else "?"
                scorer = player_name_for_id(state, goal.scorer_id)
                scorer_text = f" {scorer}" if scorer else ""
                print(f"  {number}. {goal.minute}' {team_name}{scorer_text}")
            return

        try:
            choice = int(parts[1])
        except ValueError:
            print("❌ Uzycie: var <numer gola>")
            return

        match = next((goal for number, goal in goals if number == choice), None)
        if match is None:
            print(f"❌ Gol numer '{choice}' nie istnieje.")
            return

        contest.reverse_event(match.event_id, reason="var")
        print(f"✅ VAR: gol z {match.minute}' anulowany.")

    def get_start_command(self) -> Optional[Command]:
        return StartMatch()
