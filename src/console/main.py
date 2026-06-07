import sys
from typing import List, cast
from src.core.engine import SportsSystemEngine
from src.sports.darts.state import DartsContestState
from src.sports.darts.ruleset import DartsRuleSet
from src.core.contest import Contest
from src.core.contestant import Contestant, IndividualPlayer
from src.sports.darts.commands import StartDartsMatchCommand, ThrowDartCommand, OcheFaultCommand
from src.console.darts_view import DartsConsoleView

def print_menu() -> None:
    print("\n=== SDM SPORTS SYSTEM ENGINE ===")
    print("1. Register Global Player")
    print("2. Start New Darts Match (Dynamic Setup)")
    print("3. Resume Suspended Match")
    print("4. View Registered Players")
    print("5. View Match History (Archived Matches)")
    print("6. Exit System")
    print("==================================")

def match_loop(engine: SportsSystemEngine, match_id: str) -> None:
    match = engine.get_match(match_id)
    if not match:
        print("❌ Match not found in active memory!")
        return

    # Strict type cast to access Darts-specific state properties
    state = cast(DartsContestState, match.current_state)
    match.notify()
    
    while not state.is_completed:
        print("\nCommands: <sector> <mult> | '0' (Miss) | 'fault' (Oche Fault) | 'suspend' (Menu)")
        cmd_input = input(">> Action: ").strip().lower()
        
        if cmd_input == 'suspend':
            print("\n⏸️ Match Suspended. State safely cached. Returning to System Menu...")
            break
            
        elif cmd_input == 'fault':
            engine.dispatch_match_command(match_id, OcheFaultCommand())
            continue
            
        elif cmd_input == '0':
            engine.dispatch_match_command(match_id, ThrowDartCommand(0, 1))
            continue
            
        try:
            parts = cmd_input.split()
            if len(parts) != 2:
                raise ValueError("Requires exactly two numbers (e.g., '20 3').")
            
            sector = int(parts[0])
            multiplier = int(parts[1])
            
            command = ThrowDartCommand(sector, multiplier)
            engine.dispatch_match_command(match_id, command)
            
        except ValueError as e:
            print(f"⚠️ Input Error: {e}")
        except Exception as e:
            print(f"⚠️ Domain Rule Rejected: {e}")
            
    if state.is_completed:
        print("\n🎉 Match Complete!")
        engine.archive_match(match_id)
        print("✅ Match archived successfully. Returning to System Menu...")

def main() -> None:
    engine = SportsSystemEngine()
    
    engine.create_individual_player("Luke Littler", metadata={"nickname": "The Nuke"})
    engine.create_individual_player("Phil Taylor", metadata={"nickname": "The Power"})
    engine.create_individual_player("Michael van Gerwen", metadata={"nickname": "MvG"})
    
    while True:
        print_menu()
        choice = input("Select operation: ").strip()
        
        if choice == '1':
            name = input("Enter player name: ").strip()
            nickname = input("Enter nickname (optional): ").strip()
            metadata = {"nickname": nickname} if nickname else {}
            
            p = engine.create_individual_player(name, metadata=metadata)
            print(f"✅ Player '{p.display_name}' registered globally.")
            
        elif choice == '2':
            players: List[Contestant] = list(engine.global_players.values())
            if len(players) < 2:
                print("❌ Insufficient players. Register at least 2 players first.")
                continue
            
            print("\n--- Match Setup ---")
            try:
                num_players = int(input(f"How many players? (min 2, max {len(players)}): ").strip())
                if num_players < 2 or num_players > len(players):
                    print("❌ Invalid number of players.")
                    continue
                
                selected_players: List[Contestant] = []
                for i in range(num_players):
                    print("\nAvailable Roster:")
                    for idx, pl in enumerate(players):
                        if pl not in selected_players:
                            nick = getattr(pl, "metadata", {}).get("nickname", "")
                            nick_str = f" '{nick}' " if nick else " "
                            print(f"[{idx}] {pl.name}{nick_str}(ID: {pl.id[:8]})")
                    
                    p_idx = int(input(f"Select Player {i + 1} Index: ").strip())
                    
                    # Strict Type Cast: Tell MyPy this Contestant is explicitly an IndividualPlayer
                    selected_player = cast(IndividualPlayer, players[p_idx])
                    selected_players.append(selected_player)

                start_score = int(input("\nStarting Score (e.g., 301, 501, 701): ").strip())
                
                if (start_score - 1) % 100 != 0:
                    print(f"\n⚠️ WARNING: {start_score} is not a standard X01 starting score (e.g., 301, 501).")
                    print("   Match will proceed, but please verify your tournament rules.")
                
                sets = int(input("Sets to win match: ").strip())
                legs = int(input("Legs to win per set: ").strip())
                
                state = DartsContestState(
                    players=selected_players, 
                    starting_score=start_score, 
                    sets_to_win=sets, 
                    legs_to_win_set=legs
                )
                ruleset = DartsRuleSet()
                match = Contest(selected_players, state, ruleset)
                match.attach(DartsConsoleView())
                
                engine.register_active_match(match)
                engine.dispatch_match_command(match.id, StartDartsMatchCommand())
                
                match_loop(engine, match.id)
                
            except (ValueError, IndexError) as e:
                print(f"❌ Invalid setup selection: {e}")

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
            for player_base in engine.global_players.values():
                # Strict Type Cast for the iteration
                ind_player = cast(IndividualPlayer, player_base)
                nick = getattr(ind_player, "metadata", {}).get("nickname", "N/A")
                print(f"- {ind_player.name} (Nickname: {nick}) | ID: {ind_player.id[:8]}")
                
        elif choice == '5':
            print("\n--- Match History (Archived) ---")
            if not engine.archived_matches:
                print("No matches have been completed yet.")
                continue
                
            for mid, m in engine.archived_matches.items():
                # Strict Type Cast for the archived state
                archived_state = cast(DartsContestState, m.current_state)
                desc = " vs ".join([pl.name for pl in archived_state.players])
                print(f"\nMatch: {desc} (ID: {mid[:8]})")
                print(f"Format: {archived_state.starting_score} Up | Best of {archived_state.sets_to_win} Sets")
                print("Final Scoreboard:")
                
                for pl in archived_state.players:
                    # Strict Type Cast for the internal loop
                    pl_ind = cast(IndividualPlayer, pl)
                    print(f"  - {pl_ind.name}: {archived_state.sets_won[pl_ind.id]} Sets, {archived_state.legs_won[pl_ind.id]} Legs")
            print("--------------------------------")
                
        elif choice == '6':
            print("Shutting down SDM Sports Engine. Goodbye!")
            sys.exit(0)
            
        else:
            print("❌ Unknown command.")

if __name__ == "__main__":
    main()