from typing import Optional

from src.core.contest import Contest
from src.core.contest.command import Command, ReverseDecision
from src.console.reversal_catalog import (
    format_reversal_menu,
    parse_reversal_choice,
    resolve_catalog_choice,
)
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor
from src.sports.darts.console.darts_console_view import DartsConsoleView
from src.sports.darts.console.darts_timeline import print_darts_timeline
from src.sports.darts.console.reversal_catalog import (
    build_darts_reversal_catalog,
    darts_reverse_command,
)
from src.sports.darts.contest.commands import CallOcheFault, StartMatch, ThrowDart
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT


class DartsConsoleAdapter(ConsoleAdapter):
    @property
    def descriptor(self) -> SportDescriptor:
        return DARTS_SPORT

    def collect_config(self) -> DartsMatchConfig:
        print("\nConfig: 1. Domyslny (501)  2. Szybki (301)  3. Wlasny")
        choice = input("Choice [Default 1]: ").strip() or "1"
        if choice == "2":
            return DartsMatchConfig.quick_301()
        if choice != "3":
            return DartsMatchConfig.standard_501()

        start_score = int(input("\nStarting Score (e.g., 301, 501, 701): ").strip())
        if (start_score - 1) % 100 != 0:
            print(f"\n⚠️ WARNING: {start_score} is not a standard X01 starting score.")

        sets = int(input("Sets to win match: ").strip())
        legs = int(input("Legs to win per set: ").strip())

        in_mult_str = input(
            "In-Multiplier (1=Straight, 2=Double, 3=Triple) [Default 1]: "
        ).strip()
        in_mult = int(in_mult_str) if in_mult_str else 1

        out_mult_str = input(
            "Out-Multiplier (1=Straight, 2=Double, 3=Triple) [Default 2]: "
        ).strip()
        out_mult = int(out_mult_str) if out_mult_str else 2

        return DartsMatchConfig(
            starting_score=start_score,
            sets_to_win_match=sets,
            legs_to_win_set=legs,
            in_multiplier=in_mult,
            out_multiplier=out_mult,
        )

    def attach_view(self, contest: Contest) -> None:
        contest.detach_instances_of(DartsConsoleView)
        contest.attach(DartsConsoleView())
        if contest.current_state.match_started:
            contest.notify(None)

    def get_input_prompt(self, contest: Contest) -> str:
        return (
            "Action ('<sector> <mult>', '0', 'fault', 'log', 'reverse [nr]', 'suspend')"
        )

    def parse_command(self, user_input: str, contest: Contest) -> Optional[Command]:
        cleaned = user_input.strip().lower()

        if cleaned == "log":
            print_darts_timeline(contest)
            return None

        if cleaned.split()[0] in {"reverse", "rev"}:
            return self._parse_reversal_command(cleaned, contest)

        if cleaned == "fault":
            return CallOcheFault()

        parts = cleaned.split()
        if len(parts) == 1 and parts[0] == "0":
            return ThrowDart(sector=0, multiplier=1)

        if len(parts) == 2 and isinstance(contest.current_state, DartsContestState):
            try:
                sector = int(parts[0])
                multiplier = int(parts[1])

                valid_sectors = [0] + list(range(1, 21)) + [25, 50]
                if sector not in valid_sectors:
                    print(f"❌ '{sector}' is not valid (0-20, 25, 50).")
                    return None
                if multiplier not in [1, 2, 3]:
                    print(f"❌ '{multiplier}' is not a valid multiplier.")
                    return None
                if sector in [25, 50] and multiplier == 3:
                    print("❌ You cannot score a Treble Bullseye!")
                    return None

                return ThrowDart(sector=sector, multiplier=multiplier)
            except ValueError:
                pass

        print(
            "❌ Invalid syntax. Enter 'sector mult' (e.g., '20 3'), "
            "'0', 'fault', or 'reverse [nr]'."
        )
        return None

    def _parse_reversal_command(
        self, cleaned: str, contest: Contest
    ) -> Optional[ReverseDecision]:
        state = contest.current_state
        if not isinstance(state, DartsContestState):
            return None

        catalog = build_darts_reversal_catalog(contest, state)
        parts = cleaned.split()

        if len(parts) == 1:
            for line in format_reversal_menu(
                catalog,
                title="Zdarzenia do wycofania",
                usage="reverse <numer>",
                empty_label="(brak zdarzen do wycofania)",
            ):
                print(line)
            return None

        choice = parse_reversal_choice(parts)
        if choice is None:
            print("❌ Uzycie: reverse <numer>")
            return None

        option = resolve_catalog_choice(catalog, choice)
        if option is None:
            print(f"❌ Zdarzenie numer '{parts[1]}' nie istnieje.")
            return None

        print(f"✅ Wycofano zdarzenie nr {choice}.")
        return darts_reverse_command(option.event_id)

    def get_start_command(self) -> Optional[Command]:
        return StartMatch()

    def format_archived_match_lines(self, match_id: str, contest: Contest) -> list[str]:
        state = contest.current_state
        if not isinstance(state, DartsContestState):
            return []
        from src.sports.darts.console.archive_view import (
            format_darts_archived_match_lines,
        )

        return format_darts_archived_match_lines(match_id, contest, state)
