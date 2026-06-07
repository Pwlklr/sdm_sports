from typing import Optional, List, Any
from src.core.plugin import SportPlugin
from src.core.contest import Contest
from src.core.contestant import Contestant
from src.sports.darts.state import DartsContestState
from src.sports.darts.ruleset import DartsRuleSet
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.commands import ThrowDartCommand, OcheFaultCommand, StartDartsMatchCommand
from src.console.darts_view import DartsConsoleView
from src.core.commands import MatchCommand

class DartsPlugin(SportPlugin):
    @property
    def name(self) -> str:
        return "Professional Darts (X01)"

    def _collect_config(self) -> DartsMatchConfig:
        """Internal helper to prompt for Darts-specific settings."""
        start_score = int(input("\nStarting Score (e.g., 301, 501, 701): ").strip())
        if (start_score - 1) % 100 != 0:
            print(f"\n⚠️ WARNING: {start_score} is not a standard X01 starting score.")
            
        sets = int(input("Sets to win match: ").strip())
        legs = int(input("Legs to win per set: ").strip())
        
        in_mult_str = input("In-Multiplier (1=Straight, 2=Double, 3=Triple) [Default 1]: ").strip()
        in_mult = int(in_mult_str) if in_mult_str else 1
        
        out_mult_str = input("Out-Multiplier (1=Straight, 2=Double, 3=Triple) [Default 2]: ").strip()
        out_mult = int(out_mult_str) if out_mult_str else 2

        return DartsMatchConfig(
            starting_score=start_score, 
            sets_to_win_match=sets, 
            legs_to_win_set=legs,
            in_multiplier=in_mult,
            out_multiplier=out_mult
        )

    def setup_exhibition_match(self, selected_players: List[Contestant]) -> Optional[Contest]:
        try:
            config = self._collect_config()
            return self.create_tournament_match(selected_players, config)
        except ValueError:
            print("❌ Invalid input for Darts settings.")
            return None

    def setup_tournament_config(self) -> Any:
        try:
            print("\n--- Darts Tournament Rules ---")
            return self._collect_config()
        except ValueError:
            print("❌ Invalid input. Defaulting to 501, Best of 1 Set.")
            return DartsMatchConfig()

    def create_tournament_match(self, match_players: List[Contestant], config: Any) -> Contest:
        assert isinstance(config, DartsMatchConfig)
        state = DartsContestState(players=match_players, config=config)
        match = Contest(match_players, state, DartsRuleSet())
        match.attach(DartsConsoleView())
        return match

    def get_start_command(self) -> Optional[MatchCommand]:
        return StartDartsMatchCommand()

    def get_input_prompt(self, contest: Contest) -> str:
        return "Action ('<sector> <mult>', '0', 'fault', 'suspend')"

    def parse_command(self, user_input: str, contest: Contest) -> Optional[MatchCommand]:
        cleaned = user_input.strip().lower()
        
        if cleaned == "fault":
            return OcheFaultCommand()
            
        parts = cleaned.split()
        if len(parts) == 1 and parts[0] == "0":
            return ThrowDartCommand(sector=0, multiplier=1)

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

                return ThrowDartCommand(sector=sector, multiplier=multiplier)
            except ValueError:
                pass
        
        print("❌ Invalid syntax. Enter 'sector mult' (e.g., '20 3'), '0' or 'fault'.")
        return None