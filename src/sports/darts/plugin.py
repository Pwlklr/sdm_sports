from typing import Optional
from src.core.plugin import SportPlugin
from src.core.contest import Contest
from src.core.contestant import Contestant
from src.sports.darts.player import DartPlayer
from src.sports.darts.state import DartsContestState
from src.sports.darts.ruleset import DartsRuleSet
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.commands import ThrowDartCommand
from src.console.darts_view import DartsScoreboardObserver
from src.core.commands import MatchCommand

class DartsPlugin(SportPlugin):
    @property
    def name(self) -> str:
        return "Professional Darts (X01)"

    def interactive_setup(self) -> Contest:
        # In the new architecture, the Tournament Engine handles player setup.
        # This method is kept for backwards compatibility or single exhibition matches.
        players: list[Contestant] = [DartPlayer("p1", "Player 1"), DartPlayer("p2", "Player 2")]
        return self.create_match(players)

    def create_match(self, players: list[Contestant]) -> Contest:
        """Called by the Tournament Engine to generate a configured match."""
        # For simplicity in testing, we'll hardcode a fast config, 
        # but this could be pulled from a TournamentPolicy
        config = DartsMatchConfig(starting_score=301, sets_to_win_match=1, legs_to_win_set=1)
        state = DartsContestState(players=players, config=config)
        ruleset = DartsRuleSet()
        
        contest = Contest(
            contest_id="darts_match",
            teams=[], 
            initial_state=state,
            ruleset=ruleset
        )
        contest.attach(DartsScoreboardObserver())
        return contest

    def parse_command(self, user_input: str, contest: Contest) -> Optional[MatchCommand]:
        parts = user_input.split()
        if len(parts) == 2 and isinstance(contest.current_state, DartsContestState):
            try:
                sector = int(parts[0])
                multiplier = int(parts[1])
                
                # STRICT DOMAIN VALIDATION
                valid_sectors = list(range(1, 21)) + [25, 50]
                if sector not in valid_sectors:
                    print(f"❌ '{sector}' is not a valid sector on a dartboard (1-20, 25, 50).")
                    return None
                    
                if multiplier not in [1, 2, 3]:
                    print(f"❌ '{multiplier}' is not a valid multiplier. Use 1 (Single), 2 (Double), or 3 (Treble).")
                    return None
                    
                if sector in [25, 50] and multiplier == 3:
                    print("❌ You cannot score a Treble Bullseye!")
                    return None

                active_player = contest.current_state.active_player
                return ThrowDartCommand(player_id=active_player.contestant_id, sector=sector, multiplier=multiplier)
            except ValueError:
                pass
        
        print("❌ Invalid syntax. Enter 'sector multiplier' (e.g., '20 3' for Treble 20).")
        return None