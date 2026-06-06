import sys
from src.core.engine import SportsSystemEngine
from src.sports.darts.state import DartsContestState
from src.sports.darts.ruleset import DartsRuleSet
from src.core.contest import Contest
from src.sports.darts.commands import StartDartsMatchCommand, ThrowDartCommand
from src.console.darts_view import DartsConsoleView

def print_menu() -> None:
    print("\n=== SDM SPORTS SYSTEM ENGINE ===")
    print("1. Register Global Player")
    print("2. Start New Darts Match (Context: Darts)")
    print("3. Resume Suspended Match")
    print("4. View Registered Players")
    print("5. Exit System")
    print("==================================")

def match_loop(engine: SportsSystemEngine, match_id: str) -> None:
    """The localized interactive loop for a specific match."""
    match = engine.get_match(match_id)
    if not match:
        print("❌ Match not found in active memory!")
        return

    state = match.current_state
    assert isinstance(state, DartsContestState)
    
    # Trigger a UI update in case we are resuming
    match.notify()
    
    while not state.is_finished:
        print("\nCommands: <sector> <multiplier> (e.g., '20 3') | '0 1' (Miss) | 'suspend' (Menu)")
        cmd_input = input(">> Action: ").strip().lower()
        
        if cmd_input == 'suspend':
            print("\n⏸️ Match Suspended. State safely cached. Returning to System Menu...")
            break
            
        try:
            parts = cmd_input.split()
            if len(parts) != 2:
                raise ValueError("Requires exactly two numbers separated by a space.")
            
            sector = int(parts[0])
            multiplier = int(parts[1])
            
            # Dispatch the command through the Engine Facade
            command = ThrowDartCommand(sector, multiplier)
            engine.dispatch_match_command(match_id, command)
            
        except ValueError as e:
            print(f"⚠️ Input Error: {e}")
        except Exception as e:
            print(f"⚠️ Domain Rule Rejected: {e}")
            
    if state.is_finished:
        print("\n🎉 Match Complete! Returning to System Menu...")


def main() -> None:
    # Initialize the core system facade
    engine = SportsSystemEngine()
    
    # Pre-seed players for convenience
    engine.create_individual_player("Luke Littler")
    engine.create_individual_player("Phil Taylor")
    
    while True:
        print_menu()
        choice = input("Select operation: ").strip()
        
        if choice == '1':
            name = input("Enter player name: ").strip()
            p = engine.create_individual_player(name)
            print(f"✅ Player '{p.name}' registered globally.")
            
        elif choice == '2':
            players = list(engine.global_players.values())
            if len(players) < 2:
                print("❌ Insufficient players. Register at least 2 players first.")
                continue
            
            print("\n--- Match Setup ---")
            for i, p in enumerate(players):
                print(f"[{i}] {p.name}")
                
            try:
                p1_idx = int(input("Select Player 1 Index: ").strip())
                p2_idx = int(input("Select Player 2 Index: ").strip())
                p1 = players[p1_idx]
                p2 = players[p2_idx]
                
                # Setup Darts-Specific Aggregates
                state = DartsContestState([p1, p2], starting_score=301, sets_to_win=1, legs_to_win_set=1)
                ruleset = DartsRuleSet()
                match = Contest([p1, p2], state, ruleset)
                
                # Attach UI Observer
                match.attach(DartsConsoleView())
                
                # Register to Engine
                engine.register_active_match(match)
                engine.dispatch_match_command(match.id, StartDartsMatchCommand())
                
                # Enter context
                match_loop(engine, match.id)
                
            except (ValueError, IndexError):
                print("❌ Invalid selection.")

        elif choice == '3':
            active = engine.active_matches
            if not active:
                print("❌ No matches currently suspended in memory.")
                continue
                
            print("\n--- Suspended Matches ---")
            match_ids = list(active.keys())
            for i, mid in enumerate(match_ids):
                m = active[mid]
                desc = " vs ".join([p.name for p in m.contestants])
                print(f"[{i}] {desc} (ID: {mid[:8]}...)")
                
            try:
                m_idx = int(input("Select match to resume: ").strip())
                match_loop(engine, match_ids[m_idx])
            except (ValueError, IndexError):
                print("❌ Invalid selection.")
                
        elif choice == '4':
            print("\n--- Global Roster ---")
            for p in engine.global_players.values():
                print(f"- {p.name} (ID: {p.id})")
                
        elif choice == '5':
            print("Shutting down SDM Sports Engine. Goodbye!")
            sys.exit(0)
            
        else:
            print("❌ Unknown command.")

if __name__ == "__main__":
    main()