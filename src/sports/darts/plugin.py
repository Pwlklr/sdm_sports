from typing import Optional
from src.core.plugin import SportPlugin
from src.core.contest import Contest
from src.core.contestant import Contestant
from src.sports.darts.player import DartPlayer
from src.sports.darts.state import DartsContestState
from src.sports.darts.ruleset import DartsRuleSet
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.commands import ThrowDartCommand, OcheFaultCommand
from src.console.darts_view import DartsConsoleView
from src.core.commands import MatchCommand

class DartsPlugin(SportPlugin):
    @property
    def name(self) -> str:
        return "Professional Darts (X01)"

    def interactive_setup(self) -> Contest:
        players: list[Contestant] = [DartPlayer("p1", "Player 1"), DartPlayer("p2", "Player 2")]
        return self.create_match(players)

    def create_match(self, players: list[Contestant]) -> Contest:
        config = DartsMatchConfig(starting_score=301, sets_to_win_match=1, legs_to_win_set=1)
        state = DartsContestState(players=players, config=config)
        ruleset = DartsRuleSet()
        
        contest = Contest(
            contest_id="darts_match",
            contestants=players, 
            initial_state=state,
            ruleset=ruleset
        )
        contest.attach(DartsConsoleView())
        return contest

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
                
                # Valid sectors now safely explicitly include 0
                valid_sectors = [0] + list(range(1, 21)) + [25, 50]
                if sector not in valid_sectors:
                    print(f"❌ '{sector}' is not a valid sector on a dartboard (0-20, 25, 50).")
                    return None
                    
                if multiplier not in [1, 2, 3]:
                    print(f"❌ '{multiplier}' is not a valid multiplier. Use 1, 2, or 3.")
                    return None
                    
                if sector in [25, 50] and multiplier == 3:
                    print("❌ You cannot score a Treble Bullseye!")
                    return None

                return ThrowDartCommand(sector=sector, multiplier=multiplier)
            except ValueError:
                pass
        
        print("❌ Invalid syntax. Enter 'sector multiplier' (e.g., '20 3'), '0' or 'fault'.")
        return None