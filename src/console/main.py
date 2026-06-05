import sys
import random
from src.core.plugin import SportPlugin
from src.core.contestant import Contestant
from src.sports.darts.player import DartPlayer
from src.sports.darts.plugin import DartsPlugin

class TournamentEngine:
    """A generic orchestrator to handle N-Players and tournament brackets."""
    def __init__(self, plugin: SportPlugin):
        self.plugin = plugin
        self.players: list[Contestant] = []

    def register_players(self) -> None:
        print(f"\n--- {self.plugin.name} Tournament Registration ---")
        num_players = int(input("How many players are entering the tournament? (e.g., 4): ").strip() or "2")
        
        for i in range(num_players):
            name = input(f"Enter name for Player {i+1}: ").strip() or f"Player {i+1}"
            self.players.append(DartPlayer(contestant_id=f"p{i+1}", name=name))
            
        print(f"\n✅ {len(self.players)} players registered!")

    def generate_knockout_bracket(self) -> list[tuple[Contestant, Contestant]]:
        """Shuffles players and pairs them up for a Knockout phase."""
        random.shuffle(self.players)
        bracket = []
        for i in range(0, len(self.players), 2):
            if i + 1 < len(self.players):
                bracket.append((self.players[i], self.players[i+1]))
            else:
                print(f"⚠️ {self.players[i].name} gets a bye to the next round!")
        return bracket

    def play_match(self, p1: Contestant, p2: Contestant) -> Contestant:
        print(f"\n🏆 NEXT MATCH: {p1.name} vs {p2.name} 🏆")
        input("Press Enter to begin...")
        
        # Use the plugin to generate the domain match
        # If we had a CricketPlugin, it would generate a Cricket match here!
        contest = self.plugin.create_match([p1, p2])
        if hasattr(contest, 'notify'): 
            contest.notify()

        while True:
            if hasattr(contest.current_state, 'is_completed') and getattr(contest.current_state, 'is_completed'):
                winner_id = getattr(contest.current_state, 'winner_id')
                winner = p1 if p1.contestant_id == winner_id else p2
                print(f"\n🎉 {winner.name} ADVANCES IN THE TOURNAMENT! 🎉")
                return winner

            user_input = input("\n>> Command: ").strip().lower()
            if user_input == 'q':
                print("Tournament Abandoned.")
                sys.exit(0)
            
            command = self.plugin.parse_command(user_input, contest)
            if command:
                command.execute(contest)

    def run(self) -> None:
        self.register_players()
        bracket = self.generate_knockout_bracket()
        
        print("\n--- TOURNAMENT BRACKET GENERATED ---")
        for match in bracket:
            print(f" - {match[0].name} vs {match[1].name}")
            
        winners = []
        for match in bracket:
            winner = self.play_match(match[0], match[1])
            winners.append(winner)
            
        print("\n🏆 TOURNAMENT PHASE COMPLETE 🏆")
        print("Advancing Players:", [w.name for w in winners])


class SDMSportsApp:
    def __init__(self) -> None:
        self.plugins: list[SportPlugin] = [DartsPlugin()]

    def run(self) -> None:
        print("="*40)
        print(" WELCOME TO SDM SPORTS TOURNAMENT CORE")
        print("="*40)
        
        print("\nSelect Discipline:")
        for idx, plugin in enumerate(self.plugins):
            print(f"{idx + 1}. {plugin.name}")
            
        choice = input("\nEnter choice number: ").strip()
        try:
            selected_plugin = self.plugins[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid selection. Exiting.")
            sys.exit(1)

        engine = TournamentEngine(selected_plugin)
        engine.run()

if __name__ == "__main__":
    app = SDMSportsApp()
    app.run()