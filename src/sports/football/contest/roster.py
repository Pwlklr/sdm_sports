from __future__ import annotations

from src.core.contestant.models import IndividualPlayer, Team


def parse_console_team_number(token: str, team_count: int) -> int | None:
    """Parse a 1-based team number from console input; return 0-based index."""
    try:
        number = int(token)
    except ValueError:
        print("❌ Team must be a number (e.g. 1 or 2).")
        return None
    if number < 1 or number > team_count:
        print(f"❌ Team number '{number}' is out of range (1-{team_count}).")
        return None
    return number - 1


def parse_console_player_number(token: str, team: Team) -> int | None:
    """Parse a 1-based player number from console input."""
    try:
        number = int(token)
    except ValueError:
        print("❌ Player must be a number (see squad list on scoreboard).")
        return None
    if not team.roster:
        print(f"❌ {team.name} has no players on the roster.")
        return None
    if number < 1 or number > len(team.roster):
        print(
            f"❌ Player number '{number}' is out of range "
            f"(1-{len(team.roster)} on {team.name})."
        )
        return None
    return number


def resolve_roster_player_by_number(team: Team, player_number: int) -> IndividualPlayer:
    return team.roster[player_number - 1]


def player_on_team(team: Team, player_id: str) -> bool:
    return any(player.id == player_id for player in team.roster)


def format_team_header(team_number: int, team: Team) -> str:
    return f"{team_number}={team.name}"


def format_squad_lines(team: Team, indent: str = "     ") -> list[str]:
    if not team.roster:
        return [f"{indent}(empty squad)"]
    return [
        f"{indent}{player_number}. {player.name}"
        for player_number, player in enumerate(team.roster, start=1)
    ]


def parse_console_minute(token: str, max_minute: int) -> int | None:
    try:
        minute = int(token)
    except ValueError:
        print("❌ Minute must be a number (e.g. 23).")
        return None
    if minute < 0:
        print("❌ Minute cannot be negative.")
        return None
    if minute > max_minute:
        print(f"❌ Minute '{minute}' exceeds current match clock (max {max_minute}).")
        return None
    return minute


def match_clock_limit(state: object) -> int:
    from src.sports.football.contest.state import FootballContestState

    if not isinstance(state, FootballContestState):
        return 0
    total = 0
    period = state.current_period
    for p in state.periods:
        total += p.length_minutes
        if p is period and not p.is_finished:
            break
    return total


def player_name_for_id(state: object, player_id: str | None) -> str:
    from src.sports.football.contest.state import FootballContestState

    if player_id is None or not isinstance(state, FootballContestState):
        return ""
    for team in state.teams:
        if not isinstance(team, Team):
            continue
        for player in team.roster:
            if player.id == player_id:
                return player.name
    return "?"
