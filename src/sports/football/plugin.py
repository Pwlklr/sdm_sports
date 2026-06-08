from typing import Any, List, Optional

from src.console.football_view import FootballConsoleView
from src.core.commands import MatchCommand
from src.core.contest import Contest
from src.core.contestant import Contestant
from src.core.plugin import SportPlugin
from src.sports.football.commands import (
    CommitFoulCommand,
    EndPeriodCommand,
    PenaltyKickCommand,
    ScoreGoalCommand,
    StartFootballMatchCommand,
)
from src.sports.football.config import FootballMatchConfig
from src.sports.football.ruleset import FootballRuleSet
from src.sports.football.state import FootballContestState, MatchPhase


class FootballPlugin(SportPlugin):
    @property
    def name(self) -> str:
        return "Association Football (Soccer)"

    def _collect_config(self) -> FootballMatchConfig:
        """Internal helper to prompt for football-specific settings."""
        halves = int(input("\nNumber of halves [Default 2]: ").strip() or "2")
        length = int(input("Half length in minutes [Default 45]: ").strip() or "45")
        draw_str = input("Allow draws? (y/n) [Default y]: ").strip().lower()
        allow_draw = draw_str != "n"

        return FootballMatchConfig(
            number_of_halves=halves,
            half_length_minutes=length,
            allow_draw=allow_draw,
        )

    def setup_exhibition_match(
        self, selected_players: List[Contestant]
    ) -> Optional[Contest]:
        try:
            config = self._collect_config()
            return self.create_tournament_match(selected_players, config)
        except ValueError:
            print("❌ Invalid input for Football settings.")
            return None

    def setup_tournament_config(self) -> Any:
        try:
            print("\n--- Football Tournament Rules ---")
            print("(Knockout matches cannot end in a draw.)")
            return self._collect_config()
        except ValueError:
            print("❌ Invalid input. Defaulting to 2x45 minutes.")
            return FootballMatchConfig()

    def create_tournament_match(
        self, match_players: List[Contestant], config: Any
    ) -> Contest:
        assert isinstance(config, FootballMatchConfig)
        state = FootballContestState(teams=match_players, config=config)
        match = Contest(match_players, state, FootballRuleSet())
        match.attach(FootballConsoleView())
        return match

    def get_start_command(self) -> Optional[MatchCommand]:
        return StartFootballMatchCommand()

    def get_input_prompt(self, contest: Contest) -> str:
        state = contest.current_state
        if isinstance(state, FootballContestState):
            sides = " ".join(f"{i}={t.name}" for i, t in enumerate(state.teams))
            if state.phase == MatchPhase.PENALTIES:
                return f"Penalty [{sides}] ('pk <team> g|m')"
            return (
                f"Action [{sides}] ('goal <team>', 'og <team>', 'pen <team>', "
                "'yellow <team>', 'red <team>', 'foul <team>', 'end')"
            )
        return "Action"

    def parse_command(
        self, user_input: str, contest: Contest
    ) -> Optional[MatchCommand]:
        cleaned = user_input.strip().lower()
        parts = cleaned.split()
        if not parts:
            print("❌ Empty command.")
            return None

        verb = parts[0]
        state = contest.current_state
        team_count = len(state.teams) if isinstance(state, FootballContestState) else 2

        if verb == "end":
            return EndPeriodCommand()

        def parse_team_index(token: str) -> Optional[int]:
            try:
                idx = int(token)
            except ValueError:
                print("❌ Team must be an index (e.g. '0' or '1').")
                return None
            if idx < 0 or idx >= team_count:
                print(f"❌ Team index '{idx}' is out of range (0-{team_count - 1}).")
                return None
            return idx

        if verb in {"goal", "og", "pen"} and len(parts) == 2:
            idx = parse_team_index(parts[1])
            if idx is None:
                return None
            return ScoreGoalCommand(
                team_index=idx,
                own_goal=verb == "og",
                penalty=verb == "pen",
            )

        if verb in {"foul", "yellow", "red"} and len(parts) >= 2:
            idx = parse_team_index(parts[1])
            if idx is None:
                return None
            offender = parts[2] if len(parts) >= 3 else None
            card = None if verb == "foul" else verb
            return CommitFoulCommand(team_index=idx, card=card, offender_id=offender)

        if verb == "pk" and len(parts) == 3:
            idx = parse_team_index(parts[1])
            if idx is None:
                return None
            outcome = parts[2]
            if outcome not in {"g", "m"}:
                print("❌ Penalty outcome must be 'g' (goal) or 'm' (miss).")
                return None
            return PenaltyKickCommand(team_index=idx, scored=outcome == "g")

        print("❌ Invalid syntax. See the prompt for valid actions.")
        return None
