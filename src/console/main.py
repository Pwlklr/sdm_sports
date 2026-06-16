import sys
from dataclasses import replace
from typing import List

from src.core.contest import Contest
from src.core.shared.command_rejected import CommandRejected
from src.console.tournament_view import (
    active_matches,
    schedule_view,
    standings_table,
)
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.match_setup import create_console_contest
from src.core.sport.registered_sport import RegisteredSport
from src.core.contestant import Contestant, IndividualPlayer, Team
from src.core.system.sports_system_engine import SportsSystemEngine
from src.core.tournament import Tournament
from src.core.tournament.event import FixtureScheduled
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.darts.plugin import DARTS_PLUGIN
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.sports.football.plugin import FOOTBALL_PLUGIN
from src.sports.football.contest.football_contest_state import FootballContestState


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


def sport_id_for_match(match: Contest) -> str:
    state = match.current_state
    if isinstance(state, DartsContestState):
        return DARTS_SPORT.id
    if isinstance(state, FootballContestState):
        return FOOTBALL_SPORT.id
    raise ValueError("Cannot determine sport for this match.")


def select_sport(engine: SportsSystemEngine) -> RegisteredSport:
    sports = engine.get_available_sports()
    if not sports:
        print("❌ No sports registered.")
        sys.exit(1)

    print("\nSelect Discipline:")
    for i, sport in enumerate(sports):
        print(f"{i + 1}. {sport.descriptor.display_name}")

    try:
        choice = int(input("Choice: ").strip()) - 1
        return sports[choice]
    except (ValueError, IndexError):
        print("⚠️ Invalid choice, defaulting to first sport.")
        return sports[0]


def match_loop(
    engine: SportsSystemEngine, match_id: str, adapter: ConsoleAdapter
) -> None:
    match = engine.get_match(match_id)
    if not match:
        print("❌ Match not found in active memory!")
        return

    while not match.current_state.is_finished:
        prompt_text = adapter.get_input_prompt(match)
        cmd_input = input(f">> {prompt_text}: ").strip().lower()

        if cmd_input == "suspend":
            print("\n⏸️ Match Suspended. State safely cached.")
            break

        command = adapter.parse_command(cmd_input, match)
        if command:
            try:
                engine.dispatch_match_command(match_id, command)
            except CommandRejected as e:
                print(f"⛔ Odrzucono: {e.reason}")
            except ValueError as e:
                print(f"⚠️ System Error: {e}")

    if match.current_state.is_finished:
        print("\n🎉 Match Complete!")


def setup_demo_roster(engine: SportsSystemEngine) -> None:
    for name, nick in [
        ("Luke Littler", "The Nuke"),
        ("Phil Taylor", "The Power"),
        ("Michael van Gerwen", "MvG"),
        ("Gerwyn Price", "The Iceman"),
    ]:
        engine.create_individual_player(name, metadata={"nickname": nick})

    engine.create_team_with_roster(
        "Arsenal FC",
        [
            "Raya",
            "Saliba",
            "Gabriel",
            "Zinchenko",
            "White",
            "Odegaard",
            "Rice",
            "Partey",
            "Havertz",
            "Saka",
            "Jesus",
            "Ramsdale",
            "Tomiyasu",
            "Jorginho",
            "Trossard",
            "Nketiah",
        ],
    )
    engine.create_team_with_roster(
        "Manchester City",
        [
            "Ederson",
            "Walker",
            "Dias",
            "Stones",
            "Gvardiol",
            "Rodri",
            "De Bruyne",
            "Silva",
            "Foden",
            "Haaland",
            "Alvarez",
            "Ortega",
            "Akanji",
            "Kovacic",
            "Doku",
            "Grealish",
        ],
    )
    engine.create_team_with_roster(
        "Liverpool FC",
        [
            "Alisson",
            "Alexander-Arnold",
            "Konate",
            "Van Dijk",
            "Robertson",
            "Mac Allister",
            "Szoboszlai",
            "Endo",
            "Salah",
            "Nunez",
            "Diaz",
            "Kelleher",
            "Quansah",
            "Gravenberch",
            "Gakpo",
            "Jota",
        ],
    )
    engine.create_team_with_roster(
        "Chelsea FC",
        [
            "Sanchez",
            "James",
            "Colwill",
            "Disasi",
            "Chilwell",
            "Caicedo",
            "Enzo",
            "Gallagher",
            "Palmer",
            "Jackson",
            "Sterling",
            "Petrovic",
            "Badiashile",
            "Madueke",
            "Broja",
            "Nkunku",
        ],
    )


def select_players(
    engine: SportsSystemEngine, min_players: int = 2
) -> List[IndividualPlayer]:
    players = engine.list_individual_players()
    if len(players) < min_players:
        print(
            f"❌ Insufficient players. Register at least {min_players} players first."
        )
        return []

    try:
        num_players = int(
            input(
                f"How many players? (min {min_players}, max {len(players)}): "
            ).strip()
        )
        if num_players < min_players or num_players > len(players):
            print("❌ Invalid number of players.")
            return []

        selected_players: List[IndividualPlayer] = []
        while len(selected_players) < num_players:
            print("\nAvailable Roster:")
            for idx, pl in enumerate(players):
                if pl not in selected_players:
                    nick = getattr(pl, "metadata", {}).get("nickname", "")
                    nick_str = f" '{nick}' " if nick else " "
                    print(f"[{idx}] {pl.name}{nick_str}(ID: {pl.id[:8]})")

            p_idx = int(
                input(f"Select Player {len(selected_players) + 1} Index: ").strip()
            )
            if p_idx < 0 or p_idx >= len(players):
                print("❌ Invalid selection. Try again.")
                continue

            selected_player = players[p_idx]
            if selected_player in selected_players:
                print("❌ Player already selected! Choose a different unique player.")
                continue

            selected_players.append(selected_player)

        return selected_players
    except (ValueError, IndexError):
        print("❌ Invalid input.")
        return []


def select_teams(engine: SportsSystemEngine, team_count: int = 2) -> List[Team]:
    teams = engine.list_teams()
    if len(teams) < team_count:
        print(
            f"❌ Need at least {team_count} registered teams "
            f"(only {len(teams)} available)."
        )
        return []

    selected_teams: List[Team] = []
    while len(selected_teams) < team_count:
        print(f"\nSelect team {len(selected_teams) + 1} of {team_count}:")
        for idx, team in enumerate(teams):
            if team in selected_teams:
                continue
            roster = (
                ", ".join(f"{n}. {p.name}" for n, p in enumerate(team.roster, start=1))
                or "(empty squad)"
            )
            print(f"[{idx}] {team.name} — {roster}")

        try:
            t_idx = int(input("Team index: ").strip())
        except ValueError:
            print("❌ Invalid input.")
            return []

        if t_idx < 0 or t_idx >= len(teams):
            print("❌ Invalid selection. Try again.")
            continue

        team = teams[t_idx]
        if team in selected_teams:
            print("❌ Team already selected.")
            continue

        selected_teams.append(team)

    return selected_teams


def select_contestants(
    engine: SportsSystemEngine, sport: RegisteredSport, *, for_tournament: bool
) -> List[Contestant]:
    if sport.descriptor.id == FOOTBALL_SPORT.id:
        min_teams = 3 if for_tournament else 2
        teams: List[Contestant] = list(select_teams(engine, team_count=min_teams))
        return teams
    min_players = 3 if for_tournament else 2
    players: List[Contestant] = list(select_players(engine, min_players=min_players))
    return players


def play_tournament_match(
    engine: SportsSystemEngine,
    tournament: Tournament,
    match: Contest,
    adapter: ConsoleAdapter,
) -> None:
    sides = " vs ".join(c.name for c in match.contestants)
    print("\n==============================================")
    print(f" 🎯 TOURNAMENT MATCH: {sides}")
    print("==============================================")
    input("Press Enter to begin match...")

    _apply_suspension_context(tournament, match)

    engine.register_active_match(match)
    adapter.attach_view(match)
    start_cmd = adapter.get_start_command()
    if start_cmd:
        engine.dispatch_match_command(match.id, start_cmd)

    match_loop(engine, match.id, adapter)

    if not match.current_state.is_finished:
        print("\n⏸️ Match suspended. You can resume it later from this menu.")
        return

    engine.complete_tournament_match(tournament, match.id)
    engine.archive_match(match.id)


def _apply_suspension_context(tournament: Tournament, match: Contest) -> None:
    """Feed current tournament suspensions into a football match before it starts."""
    state = match.current_state
    if isinstance(state, FootballContestState):
        match.current_state = state.with_tournament_context(
            suspended_player_ids=tournament.state.discipline.suspended_ids()
        )


def run_tournament_matches(
    engine: SportsSystemEngine,
    tournament: Tournament,
    adapter: ConsoleAdapter,
) -> None:
    while not tournament.is_completed:
        phase_id = tournament.active_phase_id()
        if phase_id is None and not tournament.is_completed:
            print("❌ Tournament has no active phase.")
            return

        phase_name = phase_id or "?"
        for phase in tournament.state.phases:
            if phase.id == phase_id:
                phase_name = phase.name
                break

        playable = active_matches(tournament)
        print(f"\n=== Turniej '{tournament.name}' | Faza: {phase_name} ===")
        print("1. Rozegraj mecz")
        print("2. Tabela wynikow")
        print("3. Harmonogram i wyniki")
        print("4. Powrot do menu glownego")
        action = input("Wybor: ").strip()

        if action == "1":
            if not playable:
                print("✅ Wszystkie mecze tej fazy rozegrane.")
                continue
            print("\nMecze do rozegrania:")
            for i, match in enumerate(playable):
                sides = " vs ".join(c.name for c in match.contestants)
                print(f"[{i}] {sides}")
            try:
                pick = int(input("Wybierz mecz: ").strip())
                chosen = playable[pick]
            except (ValueError, IndexError):
                print("❌ Nieprawidlowy wybor.")
                continue
            play_tournament_match(engine, tournament, chosen, adapter)

        elif action == "2":
            print("\n--- TABELA ---")
            for line in standings_table(tournament):
                print(line)

        elif action == "3":
            print("\n--- HARMONOGRAM ---")
            for line in schedule_view(tournament):
                print(line)

        elif action == "4":
            return

        else:
            print("❌ Nieprawidlowy wybor.")


def main() -> None:
    engine = SportsSystemEngine(sports=[DARTS_PLUGIN, FOOTBALL_PLUGIN])

    setup_demo_roster(engine)

    while True:
        print_menu()
        choice = input("Select operation: ").strip()

        if choice == "1":
            name = input("Enter player name: ").strip()
            nickname = input("Enter nickname (optional): ").strip()
            metadata = {"nickname": nickname} if nickname else {}
            p = engine.create_individual_player(name, metadata=metadata)
            print(f"✅ Player '{p.display_name}' registered globally.")

        elif choice == "2":
            sport = select_sport(engine)
            print(f"\n--- {sport.descriptor.display_name} Exhibition Setup ---")

            selected = select_contestants(engine, sport, for_tournament=False)
            if not selected:
                continue

            try:
                config = sport.adapter.collect_config()
                match = create_console_contest(
                    sport.descriptor.id, sport.adapter, selected, config
                )
            except ValueError as e:
                print(f"❌ {e}")
                continue

            engine.register_active_match(match)
            start_cmd = sport.adapter.get_start_command()
            if start_cmd:
                engine.dispatch_match_command(match.id, start_cmd)

            match_loop(engine, match.id, sport.adapter)

        elif choice == "3":
            sport = select_sport(engine)
            print(f"\n--- {sport.descriptor.display_name} Tournament Setup ---")

            t_name = input("Enter Tournament Name: ").strip()
            selected = select_contestants(engine, sport, for_tournament=True)
            if not selected:
                continue

            print("\nSelect Tournament Format:")
            print("1. Knockout Bracket (Random Draw)")
            print("2. Group Stage (Round Robin)")
            format_choice = input("Choice: ").strip()

            blueprint_id = "knockout_8" if format_choice == "1" else "league"

            try:
                config = sport.adapter.collect_config()
            except ValueError:
                print("❌ Invalid tournament config.")
                continue

            tournament = engine.create_tournament(
                t_name,
                sport.descriptor.id,
                blueprint_id,
                match_config=config,
            )

            scheduled = engine.setup_tournament(tournament, selected)

            print(f"\n🏆 --- {t_name.upper()} BRACKET GENERATED --- 🏆")
            for i, event in enumerate(scheduled):
                match = tournament.get_match(event.contest_id)
                if match is None:
                    continue
                sides = " vs ".join(c.name for c in match.contestants)
                print(f" Match {i + 1}: {sides}")

            run_tournament_matches(engine, tournament, sport.adapter)

            if tournament.is_completed:
                print(f"\n🎊 TOURNAMENT '{tournament.name}' HAS CONCLUDED! 🎊")
                champion_id = tournament.state.champion_id
                if champion_id:
                    name = tournament.state.contestants.get(champion_id, champion_id)
                    print(f"Champion: {name}")

        elif choice == "4":
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
                resumed = engine.get_match(match_ids[m_idx])
                if resumed is None:
                    print("❌ Invalid selection.")
                    continue
                resumed.notify(None)
                resume_adapter = engine.get_adapter(sport_id_for_match(resumed))
                if resume_adapter is None:
                    print("❌ No console adapter available.")
                    continue
                match_loop(engine, match_ids[m_idx], resume_adapter)
            except (ValueError, IndexError, AttributeError):
                print("❌ Invalid selection.")

        elif choice == "5":
            print("\n--- Global Roster ---")
            individuals = engine.list_individual_players()
            if individuals:
                print("\nIndividual players (darts):")
                for ind_player in individuals:
                    nick = ind_player.metadata.get("nickname", "N/A")
                    print(
                        f"- {ind_player.name} (Nickname: {nick}) | ID: {ind_player.id[:8]}"
                    )
            teams = engine.list_teams()
            if teams:
                print("\nTeams (football):")
                for team in teams:
                    squad = ", ".join(p.name for p in team.roster) or "(empty)"
                    print(f"- {team.name}: {squad}")
            if not individuals and not teams:
                print("No contestants registered.")

        elif choice == "6":
            print("\n--- Match History (Archived) ---")
            if not engine.archived_matches:
                print("No matches have been completed yet.")
                continue

            for mid, m in engine.archived_matches.items():
                state = m.current_state
                if isinstance(state, DartsContestState):
                    desc = " vs ".join([pl.name for pl in state.players])
                    print(f"\nMatch: {desc} (ID: {mid[:8]})")
                    print(
                        f"Format: {state.config.starting_score} Up | Best of {state.config.sets_to_win_match} Sets"
                    )
                    print("Final Scoreboard:")
                    for pl in state.players:
                        print(
                            f"  - {pl.name}: {state.sets_won[pl.id]} Sets, {state.legs_won[pl.id]} Legs"
                        )
                elif isinstance(state, FootballContestState):
                    desc = " vs ".join([t.name for t in state.teams])
                    print(f"\nMatch: {desc} (ID: {mid[:8]})")
                    via = state.decided_by.replace("_", " ")
                    outcome = (
                        "Draw"
                        if state.was_draw
                        else f"{state.winner.name if state.winner else '?'} ({via})"
                    )
                    if m.result.is_overridden:
                        from src.core.tournament.ranking import (
                            describe_two_way_result,
                            single_first_place,
                        )

                        official = m.result.effective_result
                        if official is None:
                            winner_name = "?"
                        else:
                            label = describe_two_way_result(official.ranking())
                            if label == "remis":
                                winner_name = "Remis"
                            elif label.startswith("wygral "):
                                winner_name = label.removeprefix("wygral ")
                            else:
                                winner = single_first_place(official.ranking())
                                winner_name = winner.name if winner else "?"
                        print(
                            f"Official Result: {winner_name} ({m.result.override_reason})"
                        )
                        print(f"Played Result: {outcome}")
                    else:
                        print(f"Result: {outcome}")
                    print("Final Score:")
                    for t in state.teams:
                        print(f"  - {t.name}: {state.scores[t.id]} goals")
                else:
                    desc = " vs ".join([c.name for c in m.contestants])
                    print(f"\nMatch: {desc} (ID: {mid[:8]})")
            print("--------------------------------")

        elif choice == "7":
            print("Shutting down SDM Sports Engine. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
