from __future__ import annotations

from src.core.contestant.models import Team


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
