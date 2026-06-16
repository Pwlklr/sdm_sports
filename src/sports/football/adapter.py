from typing import Optional

from src.core.contest import Contest
from src.core.contest.command import Command, ReverseDecision
from src.console.reversal_catalog import (
    format_reversal_menu,
    parse_reversal_choice,
    resolve_catalog_choice,
)
from src.core.contestant.models import Team
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor
from src.sports.football.console.football_command_parser import parse_football_command
from src.sports.football.console.football_console_view import FootballConsoleView
from src.sports.football.console.match_timeline import print_match_timeline
from src.sports.football.console.reversal_catalog import (
    build_football_reversal_catalog,
    football_reverse_command,
)
from src.sports.football.contest.commands import StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.console.roster_view import format_team_header
from src.sports.football.contest.football_contest_state import (
    FootballContestState,
    MatchPhase,
)
from src.sports.football.descriptor import FOOTBALL_SPORT


class FootballConsoleAdapter(ConsoleAdapter):
    @property
    def descriptor(self) -> SportDescriptor:
        return FOOTBALL_SPORT

    def collect_config(self) -> FootballMatchConfig:
        print("\nConfig: 1. Default (FIFA)  2. League  3. Cup  4. Custom")
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
        contest.detach_instances_of(FootballConsoleView)
        contest.attach(FootballConsoleView())
        if contest.current_state.match_started:
            contest.notify(None)

    def get_input_prompt(self, contest: Contest) -> str:
        state = contest.current_state
        if isinstance(state, FootballContestState):
            sides = " ".join(
                format_team_header(n, t)
                for n, t in enumerate(state.teams, start=1)
                if isinstance(t, Team)
            )
            if state.phase == MatchPhase.PENALTIES:
                return f"Penalty [{sides}] ('pk <team> g|m', 'end', 'reverse [nr]')"
            return (
                f"Action [{sides}] "
                "('goal/og/pen <t> <min> [player]', "
                "'yellow/red/foul <t> <player> <min> [reason]', "
                "'lineup <t> <players...>', 'sub <t> <out> <in> [min]', "
                "'roster [team]', 'log', 'reverse [nr]', 'var [nr]', 'end')"
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

        if verb in {"reverse", "rev"}:
            return self._parse_reversal_command(
                cleaned, contest, state, goals_only=False, verb="reverse"
            )

        if verb == "var":
            return self._parse_reversal_command(
                cleaned, contest, state, goals_only=True, verb="var"
            )

        return parse_football_command(user_input, state)

    def _parse_reversal_command(
        self,
        cleaned: str,
        contest: Contest,
        state: FootballContestState,
        *,
        goals_only: bool,
        verb: str,
    ) -> Optional[ReverseDecision]:
        catalog = build_football_reversal_catalog(contest, state, goals_only=goals_only)
        parts = cleaned.split()

        if len(parts) == 1:
            title = (
                "VAR: choose goal to disallow"
                if goals_only
                else "Events to reverse"
            )
            for line in format_reversal_menu(
                catalog,
                title=title,
                usage=f"{verb} <number>",
                empty_label="(no events to reverse)",
            ):
                print(line)
            return None

        choice = parse_reversal_choice(parts)
        if choice is None:
            print(f"❌ Usage: {verb} <number>")
            return None

        option = resolve_catalog_choice(catalog, choice)
        if option is None:
            print(f"❌ Event number '{parts[1]}' does not exist.")
            return None

        reason = "var" if goals_only else "reverse"
        print(f"✅ Reversed event #{choice}.")
        return football_reverse_command(contest, option.event_id, reason=reason)

    def get_start_command(self) -> Optional[Command]:
        return StartMatch()

    def format_archived_match_lines(self, match_id: str, contest: Contest) -> list[str]:
        state = contest.current_state
        if not isinstance(state, FootballContestState):
            return []
        from src.sports.football.console.archive_view import (
            format_football_archived_match_lines,
        )

        return format_football_archived_match_lines(match_id, contest, state)
