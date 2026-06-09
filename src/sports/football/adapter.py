from typing import Optional

from src.core.contest import Contest
from src.core.contest.command import Command
from src.core.contestant.models import Team
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor
from src.sports.football.console.football_command_parser import parse_football_command
from src.sports.football.console.football_console_view import FootballConsoleView
from src.sports.football.contest.commands import StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.roster import format_team_header
from src.sports.football.contest.state import FootballContestState, MatchPhase
from src.sports.football.descriptor import FOOTBALL_SPORT


class FootballConsoleAdapter(ConsoleAdapter):
    @property
    def descriptor(self) -> SportDescriptor:
        return FOOTBALL_SPORT

    def collect_config(self) -> FootballMatchConfig:
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
                "'roster [team]', 'end')"
            )
        return "Action"

    def parse_command(self, user_input: str, contest: Contest) -> Optional[Command]:
        state = contest.current_state
        if not isinstance(state, FootballContestState):
            return None
        return parse_football_command(user_input, state)

    def get_start_command(self) -> Optional[Command]:
        return StartMatch()
