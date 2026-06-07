import sys
from typing import List, cast
from src.core.engine import SportsSystemEngine
from src.core.contestant import Contestant, IndividualPlayer
from src.core.plugin import SportPlugin

# Tournament Rules Setup
from src.core.tournament_phase import TournamentPhase, KnockoutPhase, GroupPhase
from src.core.draw_strategies import RandomDrawStrategy, RoundRobinDrawStrategy

# Bootstrap Plugin Registration (The ONLY place specific sports are loaded)
from src.sports.darts.plugin import DartsPlugin
from src.sports.darts.state import DartsContestState

def print_menu() -> None:
    print("\n=== SDM SPORTS SYSTEM ENGINE ===")
    print("1. Register Global Player")
    print("2. Start Exhibition Match")
    print("3. Create Tournament (Multi-Match)")
    print("4. Resume Suspended Match")
    print("5. View Global Roster")
    print("6. View Archived Matches & Tournaments")
    print("7. Exit System")
    print("==================================")

def select_plugin(engine: SportsSystemEngine) -> SportPlugin:
    plugins = engine.get_available_plugins()
    if not plugins:
        print("❌ No sport plugins registered.")
        sys.exit(1)
        
    print("\nSelect Discipline:")
    for i, p in enumerate(plugins):
        print(f"{i + 1}. {p.name}")
        
    try:
        choice = int(input("Choice: ").strip()) - 1
        return plugins[choice]
    except (ValueError, IndexError):
        print("⚠️ Invalid choice, defaulting to first plugin.")
        return plugins[0]

def match_loop(engine: SportsSystemEngine, match_id: str, plugin: SportPlugin) -> None:
    """A completely generic match loop delegated to the injected Plugin."""
    match = engine.get_match(match_id)
    if not match:
        print("❌ Match not found in active memory!")
        return

    while not match.current_state.is_completed:
        prompt_text = plugin.get_input_prompt(match)
        cmd_input = input(f">> {prompt_text}: ").strip().lower()
        
        if cmd_input == 'suspend':
            print("\n⏸️ Match Suspended. State safely cached.")
            break
            
        command = plugin.parse_command(cmd_input, match)
        if command:
            try:
                engine.dispatch_match_command(match_id, command)
            except ValueError as e:
                print(f"⚠️ System Error: {e}")
            except Exception as e:
                print(f"⚠️ Domain Rule Rejected: {e}")
            
    if match.current_state.is_completed:
        print("\n🎉 Match Complete!")
        engine.archive_match(match_id)

def select_players(engine: SportsSystemEngine, min_players: int = 2) -> List[Contestant]:
    players: List[Contestant] = list(engine.global_players.values())
    if len(players) < min_players:
        print(f"❌ Insufficient players. Register at least {min_players} players first.")
        return []
    
    try:
        num_players = int(input(f"How many players? (min {min_players}, max {len(players)}): ").strip())
        if num_players < min_players or num_players > len(players):
            print("❌ Invalid number of players.")
            return []
            
        selected_players: List[Contestant] = []
        while len(selected_players) < num_players:
            print("\nAvailable Roster:")
            for idx, pl in enumerate(players):
                if pl not in selected_players:
                    nick = getattr(pl, "metadata", {}).get("nickname", "")
                    nick_str = f" '{nick}' " if nick else " "
                    print(f"[{idx}] {pl.name}{nick_str}(ID: {pl.id[:8]})")
            
            p_idx = int(input(f"Select Player {len(selected_players) + 1} Index: ").strip())
            if p_idx < 0 or p_idx >= len(players):
                print("❌ Invalid selection. Try again.")
                continue
                
            selected_player = cast(IndividualPlayer, players[p_idx])
            if selected_player in selected_players:
                print("❌ Player already selected! Choose a different unique player.")
                continue
                
            selected_players.append(selected_player)
            
        return selected_players
    except (ValueError, IndexError):
        print("❌ Invalid input.")
        return []

def main() -> None:
    engine = SportsSystemEngine()
    engine.register_plugin(DartsPlugin())
    
    engine.create_individual_player("Luke Littler", metadata={"nickname": "The Nuke"})
    engine.create_individual_player("Phil Taylor", metadata={"nickname": "The Power"})
    engine.create_individual_player("Michael van Gerwen", metadata={"nickname": "MvG"})
    engine.create_individual_player("Gerwyn Price", metadata={"nickname": "The Iceman"})
    
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
            plugin = select_plugin(engine)
            print(f"\n--- {plugin.name} Exhibition Setup ---")
            
            selected_players = select_players(engine, min_players=2)
            if not selected_players: continue
                
            match = plugin.setup_exhibition_match(selected_players)
            if not match: continue
                
            engine.register_active_match(match)
            start_cmd = plugin.get_start_command()
            if start_cmd:
                engine.dispatch_match_command(match.id, start_cmd)
            
            match_loop(engine, match.id, plugin)

        elif choice == '3':
            plugin = select_plugin(engine)
            print(f"\n--- {plugin.name} Tournament Setup ---")
            
            t_name = input("Enter Tournament Name: ").strip()
            selected_players = select_players(engine, min_players=3)
            if not selected_players: continue
                
            print("\nSelect Tournament Format:")
            print("1. Knockout Bracket (Random Draw)")
            print("2. Group Stage (Round Robin)")
            format_choice = input("Choice: ").strip()
            
            config = plugin.setup_tournament_config()
            tournament = engine.create_tournament(t_name)
            for pl in selected_players:
                tournament.register_contestant(pl)
            
            # Inline ternary initialization cleanly satisfies variable type limits
            phase: TournamentPhase = KnockoutPhase("Playoffs", RandomDrawStrategy()) if format_choice == '1' else GroupPhase("Group Stage", RoundRobinDrawStrategy())
            
            tournament.add_phase(phase)
            matchups = phase.get_matchups(selected_players)
            
            print(f"\n🏆 --- {t_name.upper()} BRACKET GENERATED --- 🏆")
            for i, (p1, p2) in enumerate(matchups):
                print(f" Match {i+1}: {p1.name} vs {p2.name}")
            
            for i, (p1, p2) in enumerate(matchups):
                print(f"\n==============================================")
                print(f" 🎯 TOURNAMENT MATCH {i+1} OF {len(matchups)}")
                print(f" UP NEXT: {p1.name} vs {p2.name}")
                print(f"==============================================")
                input("Press Enter to begin match...")
                
                match = plugin.create_tournament_match([p1, p2], config)
                engine.register_active_match(match)
                phase.add_contest(match)
                
                start_cmd = plugin.get_start_command()
                if start_cmd:
                    engine.dispatch_match_command(match.id, start_cmd)
                
                match_loop(engine, match.id, plugin)
                
                if not match.current_state.is_completed:
                    print(f"\n⏸️ Tournament '{tournament.name}' paused. Return to menu.")
                    break
                    
            tournament.advance_phase()
            if tournament.is_completed:
                print(f"\n🎊 TOURNAMENT '{tournament.name}' HAS CONCLUDED! 🎊")

        elif choice == '4':
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
                engine.get_match(match_ids[m_idx]).notify() 
                match_loop(engine, match_ids[m_idx], engine.get_available_plugins()[0])
            except (ValueError, IndexError, AttributeError):
                print("❌ Invalid selection.")
                
        elif choice == '5':
            print("\n--- Global Roster ---")
            for player_base in engine.global_players.values():
                ind_player = cast(IndividualPlayer, player_base)
                nick = getattr(ind_player, "metadata", {}).get("nickname", "N/A")
                print(f"- {ind_player.name} (Nickname: {nick}) | ID: {ind_player.id[:8]}")
                
        elif choice == '6':
            print("\n--- Match History (Archived) ---")
            if not engine.archived_matches:
                print("No matches have been completed yet.")
                continue
                
            for mid, m in engine.archived_matches.items():
                archived_state = cast(DartsContestState, m.current_state)
                desc = " vs ".join([pl.name for pl in archived_state.players])
                print(f"\nMatch: {desc} (ID: {mid[:8]})")
                print(f"Format: {archived_state.starting_score} Up | Best of {archived_state.sets_to_win} Sets")
                print("Final Scoreboard:")
                
                for pl in archived_state.players:
                    pl_ind = cast(IndividualPlayer, pl)
                    print(f"  - {pl_ind.name}: {archived_state.sets_won[pl_ind.id]} Sets, {archived_state.legs_won[pl_ind.id]} Legs")
            print("--------------------------------")
                
        elif choice == '7':
            print("Shutting down SDM Sports Engine. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()