import sys
from typing import List

from src.console.archive_view import (
    archived_matches_view,
    archived_tournaments_view,
)
from src.console.match_setup import create_console_contest
from src.console.tournament_view import (
    active_matches,
    match_session_tag,
    schedule_view,
    standings_table,
)
from src.core.contest import Contest
from src.core.contest.contest_session import ContestSessionStatus
from src.core.contestant.models import Contestant, IndividualPlayer, Team
from src.core.shared.command_rejected import CommandRejected
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.registered_sport import RegisteredSport
from src.core.system.sports_system_engine import SportsSystemEngine
from src.core.tournament import Tournament
from src.core.tournament.tournament_entry import TournamentEntry
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.darts.plugin import DARTS_PLUGIN
from src.sports.football.contest.football_contest_state import FootballContestState
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.sports.football.plugin import FOOTBALL_PLUGIN


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
        print("No sports registered.")
        sys.exit(1)

    print("\nSelect Discipline:")
    for i, sport in enumerate(sports):
        print(f"{i + 1}. {sport.descriptor.display_name}")

    try:
        choice = int(input("Choice: ").strip()) - 1
        return sports[choice]
    except (ValueError, IndexError):
        print("Invalid choice, defaulting to first sport.")
        return sports[0]


def match_loop(
    engine: SportsSystemEngine, match_id: str, adapter: ConsoleAdapter
) -> None:
    match = engine.get_match(match_id)
    if not match:
        print("Match not found in active memory!")
        return

    while not match.current_state.is_finished:
        prompt_text = adapter.get_input_prompt(match)
        cmd_input = input(f">> {prompt_text}: ").strip().lower()

        if cmd_input == "suspend":
            try:
                engine.suspend_match(match_id)
            except ValueError as e:
                print(f"System Error: {e}")
                continue
            print("\nMatch Suspended. State safely cached.")
            break

        command = adapter.parse_command(cmd_input, match)
        if command:
            try:
                engine.dispatch_match_command(match_id, command)
            except CommandRejected as e:
                print(f"Rejected: {e.reason}")
            except ValueError as e:
                print(f"System Error: {e}")

    if match.current_state.is_finished:
        print("\nMatch Complete!")


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
        print(f"Insufficient players. Register at least {min_players} players first.")
        return []

    try:
        num_players = int(
            input(
                f"How many players? (min {min_players}, max {len(players)}): "
            ).strip()
        )
        if num_players < min_players or num_players > len(players):
            print("Invalid number of players.")
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
                print("Invalid selection. Try again.")
                continue

            selected_player = players[p_idx]
            if selected_player in selected_players:
                print("Player already selected! Choose a different unique player.")
                continue

            selected_players.append(selected_player)

        return selected_players
    except (ValueError, IndexError):
        print("Invalid input.")
        return []


def select_teams(engine: SportsSystemEngine, team_count: int = 2) -> List[Team]:
    teams = engine.list_teams()
    if len(teams) < team_count:
        print(
            f"Need at least {team_count} registered teams "
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
            print(f"[{idx}] {team.name} - {roster}")

        try:
            t_idx = int(input("Team index: ").strip())
        except ValueError:
            print("Invalid input.")
            return []

        if t_idx < 0 or t_idx >= len(teams):
            print("Invalid selection. Try again.")
            continue

        team = teams[t_idx]
        if team in selected_teams:
            print("Team already selected.")
            continue

        selected_teams.append(team)

    return selected_teams


def select_squad_from_team(
    team: Team, *, min_players: int = 14, max_players: int = 23
) -> tuple[str, ...]:
    if len(team.roster) < min_players:
        print(
            f"{team.name} has only {len(team.roster)} players; "
            f"need at least {min_players} for a tournament squad."
        )
        return ()

    print(f"\n--- Tournament squad for {team.name} ---")
    for number, player in enumerate(team.roster, start=1):
        print(f"  {number}. {player.name}")

    while True:
        raw = input(
            f"Enter squad player numbers (comma-separated, "
            f"min {min_players}, max {max_players}): "
        ).strip()
        try:
            numbers = [int(part.strip()) for part in raw.split(",") if part.strip()]
        except ValueError:
            print("Invalid input.")
            continue
        if len(numbers) < min_players or len(numbers) > max_players:
            print(
                f"Squad must contain between {min_players} and {max_players} players."
            )
            continue
        if len(set(numbers)) != len(numbers):
            print("Duplicate player numbers are not allowed.")
            continue

        player_ids: list[str] = []
        invalid = False
        for number in numbers:
            if number < 1 or number > len(team.roster):
                print(f"Invalid player number: {number}.")
                invalid = True
                break
            player_ids.append(team.roster[number - 1].id)
        if invalid:
            continue
        return tuple(player_ids)


def select_tournament_entries(
    engine: SportsSystemEngine, sport: RegisteredSport
) -> List[TournamentEntry]:
    if sport.descriptor.id == FOOTBALL_SPORT.id:
        teams = select_teams(engine, team_count=3)
        if len(teams) < 3:
            return []
        entries: List[TournamentEntry] = []
        for team in teams:
            if not isinstance(team, Team):
                continue
            player_ids = select_squad_from_team(team)
            if not player_ids:
                return []
            entries.append(TournamentEntry(contestant=team, player_ids=player_ids))
        return entries

    players = select_players(engine, min_players=3)
    return [
        TournamentEntry(contestant=player, player_ids=(player.id,))
        for player in players
    ]


def ensure_football_lineups(
    engine: SportsSystemEngine, match_id: str, adapter: ConsoleAdapter
) -> bool:
    match = engine.get_match(match_id)
    if match is None:
        return False
    state = match.current_state
    if not isinstance(state, FootballContestState) or not state.eligible_player_ids:
        return True

    while not state.match_started:
        missing = [team for team in state.teams if state.lineup_for(team.id) is None]
        if not missing:
            return True
        team = missing[0]
        print(
            f"\nSubmit match squad for {team.name} "
            f"(use: lineup <team#> <player#...>)."
        )
        adapter.attach_view(match)
        cmd_input = input(f">> {adapter.get_input_prompt(match)}: ").strip().lower()
        if cmd_input in {"quit", "exit", "q"}:
            return False
        command = adapter.parse_command(cmd_input, match)
        if command is None:
            continue
        try:
            engine.dispatch_match_command(match_id, command)
        except CommandRejected as error:
            print(f"Rejected: {error.reason}")
        match = engine.get_match(match_id)
        if match is None:
            return False
        state = match.current_state
        if not isinstance(state, FootballContestState):
            return False
    return True


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
    status = match.session_status
    is_resume = status in (
        ContestSessionStatus.SUSPENDED,
        ContestSessionStatus.IN_PROGRESS,
    )

    print("\n==============================================")
    if status is ContestSessionStatus.SUSPENDED:
        print(f" TOURNAMENT MATCH (RESUME): {sides}")
    elif is_resume:
        print(f" TOURNAMENT MATCH (CONTINUE): {sides}")
    else:
        print(f" TOURNAMENT MATCH: {sides}")
    print("==============================================")

    if is_resume:
        input("Press Enter to continue match...")
        if match.is_suspended:
            match.resume()
    else:
        input("Press Enter to begin match...")

    engine.sync_match_discipline(tournament, match)

    engine.register_active_match(match)
    adapter.attach_view(match)

    if not match.current_state.match_started:
        if not ensure_football_lineups(engine, match.id, adapter):
            return
        start_cmd = adapter.get_start_command()
        if start_cmd:
            try:
                engine.dispatch_match_command(match.id, start_cmd)
            except CommandRejected as e:
                print(f"Rejected: {e.reason}")
                return

    match_loop(engine, match.id, adapter)

    if match.session_status is ContestSessionStatus.SUSPENDED:
        print("\nMatch suspended. Select it again from the tournament menu to resume.")
        return

    if not match.current_state.is_finished:
        return

    engine.complete_tournament_match(tournament, match.id)
    engine.archive_match(match.id)


def run_tournament_matches(
    engine: SportsSystemEngine,
    tournament: Tournament,
    adapter: ConsoleAdapter,
) -> None:
    while not tournament.is_completed:
        phase_id = tournament.active_phase_id()
        if phase_id is None and not tournament.is_completed:
            print("Tournament has no active phase.")
            return

        phase_name = phase_id or "?"
        for phase in tournament.state.phases:
            if phase.id == phase_id:
                phase_name = phase.name
                break

        playable = active_matches(tournament)
        print(f"\n=== Tournament '{tournament.name}' | Phase: {phase_name} ===")
        print("1. Play match")
        print("2. Standings")
        print("3. Schedule and results")
        print("4. Back to main menu")
        action = input("Choice: ").strip()

        if action == "1":
            if not playable:
                print("All matches in this phase have been played.")
                continue
            print("\nMatches to play:")
            for i, match in enumerate(playable):
                sides = " vs ".join(c.name for c in match.contestants)
                print(f"[{i}] {sides}{match_session_tag(match)}")
            try:
                pick = int(input("Select match: ").strip())
                chosen = playable[pick]
            except (ValueError, IndexError):
                print("Invalid choice.")
                continue
            play_tournament_match(engine, tournament, chosen, adapter)

        elif action == "2":
            print("\n--- STANDINGS ---")
            for line in standings_table(tournament):
                print(line)

        elif action == "3":
            print("\n--- SCHEDULE ---")
            for line in schedule_view(tournament):
                print(line)

        elif action == "4":
            return

        else:
            print("Invalid choice.")


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
            print(f"Player '{p.display_name}' registered globally.")

        elif choice == "2":
            sport = select_sport(engine)
            adapter = sport.adapter
            if adapter is None:
                print("This sport has no console adapter registered.")
                continue
            print(f"\n--- {sport.descriptor.display_name} Exhibition Setup ---")

            selected = select_contestants(engine, sport, for_tournament=False)
            if not selected:
                continue

            try:
                config = adapter.collect_config()
                match = create_console_contest(
                    sport.descriptor.id, adapter, selected, config
                )
            except ValueError as e:
                print(f"{e}")
                continue

            engine.register_active_match(match)
            start_cmd = adapter.get_start_command()
            if start_cmd:
                engine.dispatch_match_command(match.id, start_cmd)

            match_loop(engine, match.id, adapter)

        elif choice == "3":
            sport = select_sport(engine)
            adapter = sport.adapter
            if adapter is None:
                print("This sport has no console adapter registered.")
                continue
            print(f"\n--- {sport.descriptor.display_name} Tournament Setup ---")

            t_name = input("Enter Tournament Name: ").strip()
            entries = select_tournament_entries(engine, sport)
            if not entries:
                continue

            print("\nSelect Tournament Format:")
            print("1. Knockout Bracket (Random Draw)")
            print("2. Group Stage (Round Robin)")
            format_choice = input("Choice: ").strip()

            blueprint_id = "knockout_8" if format_choice == "1" else "league"

            try:
                config = adapter.collect_config()
            except ValueError:
                print("Invalid tournament config.")
                continue

            tournament = engine.create_tournament(
                t_name,
                sport.descriptor.id,
                blueprint_id,
                match_config=config,
            )

            scheduled = engine.setup_tournament(tournament, entries)

            print(f"\n--- {t_name.upper()} BRACKET GENERATED ---")
            for i, event in enumerate(scheduled):
                fixture_match = tournament.get_match(event.contest_id)
                if fixture_match is None:
                    continue
                sides = " vs ".join(c.name for c in fixture_match.contestants)
                print(f" Match {i + 1}: {sides}")

            run_tournament_matches(engine, tournament, adapter)

            if tournament.is_completed:
                print(f"\nTOURNAMENT '{tournament.name}' HAS CONCLUDED!")
                champion_id = tournament.state.champion_id
                if champion_id:
                    name = tournament.state.contestants.get(champion_id, champion_id)
                    print(f"Champion: {name}")

        elif choice == "4":
            suspended_ids = [
                mid for mid, m in engine.active_matches.items() if m.is_suspended
            ]
            if not suspended_ids:
                print("No matches currently suspended in memory.")
                continue

            print("\n--- Suspended Matches ---")
            for i, mid in enumerate(suspended_ids):
                m = engine.active_matches[mid]
                desc = " vs ".join(p.name for p in m.contestants)
                print(f"[{i}] {desc} (ID: {mid[:8]}...)")

            try:
                m_idx = int(input("Select match to resume: ").strip())
                match_id = suspended_ids[m_idx]
                resumed = engine.get_match(match_id)
                if resumed is None:
                    print("Invalid selection.")
                    continue
                resumed.resume()
                resume_adapter = engine.get_adapter(sport_id_for_match(resumed))
                if resume_adapter is None:
                    print("No console adapter available.")
                    continue
                resume_adapter.attach_view(resumed)
                match_loop(engine, match_id, resume_adapter)
            except (ValueError, IndexError, AttributeError):
                print("Invalid selection.")

        elif choice == "5":
            print("\n--- Global Roster ---")
            individuals = engine.list_individual_players()
            if individuals:
                print("\nIndividual players (darts):")
                for ind_player in individuals:
                    nick = ind_player.metadata.get("nickname", "N/A")
                    print(
                        f"- {ind_player.name} (Nickname: {nick}) | "
                        f"ID: {ind_player.id[:8]}"
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
            for line in archived_matches_view(engine):
                print(line)
            for line in archived_tournaments_view(engine):
                print(line)

        elif choice == "7":
            print("Shutting down SDM Sports Engine. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
