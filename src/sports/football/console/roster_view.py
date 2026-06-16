from __future__ import annotations

from src.core.contestant.models import Team
from src.sports.football.contest.football_contest_state import FootballContestState
from src.sports.football.contest.roster_status import (
    PlayerRosterStatus,
    roster_status_for_team,
    team_disciplinary_summary,
)


def format_team_header(team_number: int, team: Team) -> str:
    return f"{team_number}={team.name}"


def format_squad_lines(team: Team, indent: str = "     ") -> list[str]:
    if not team.roster:
        return [f"{indent}(empty squad)"]
    return [
        f"{indent}{player_number}. {player.name}"
        for player_number, player in enumerate(team.roster, start=1)
    ]


def format_player_card_suffix(status: PlayerRosterStatus) -> str:
    if status.dismissed:
        return " 🟥"
    if status.yellow_cards:
        return f" 🟨×{status.yellow_cards}"
    return ""


def _player_number(team: Team, player_id: str) -> int | None:
    for number, player in enumerate(team.roster, start=1):
        if player.id == player_id:
            return number
    return None


def _format_line_for_player(
    team: Team,
    state: FootballContestState,
    player_id: str,
    *,
    indent: str,
) -> str | None:
    number = _player_number(team, player_id)
    if number is None:
        return None
    rows = roster_status_for_team(state, team)
    row = next((r for r in rows if r.player_id == player_id), None)
    if row is None:
        return None
    return f"{indent}{row.player_number}. {row.name}{format_player_card_suffix(row)}"


def format_pitch_and_bench_lines_from_state(
    state: FootballContestState, team: Team, indent: str = "     "
) -> list[str]:
    lineup = state.lineup_for(team.id)
    if lineup is None:
        return [
            f"{indent}(lineup not submitted — use 'lineup <team> <player #...>')",
            *format_squad_lines_from_state(state, team, indent=indent),
        ]

    lines: list[str] = [f"{indent}On pitch:"]
    on_pitch_ids = sorted(
        lineup.starting,
        key=lambda pid: _player_number(team, pid) or 999,
    )
    for player_id in on_pitch_ids:
        line = _format_line_for_player(team, state, player_id, indent=f"{indent}  ")
        if line is not None:
            lines.append(line)

    lines.append(f"{indent}Bench:")
    bench_ids = sorted(
        lineup.bench,
        key=lambda pid: _player_number(team, pid) or 999,
    )
    for player_id in bench_ids:
        line = _format_line_for_player(team, state, player_id, indent=f"{indent}  ")
        if line is not None:
            lines.append(line)
    return lines


def format_squad_lines_from_state(
    state: FootballContestState, team: Team, indent: str = "     "
) -> list[str]:
    rows = roster_status_for_team(state, team)
    if not rows:
        return [f"{indent}(empty squad)"]
    return [
        f"{indent}{row.player_number}. {row.name}{format_player_card_suffix(row)}"
        for row in rows
    ]


def print_roster_report(
    state: FootballContestState, team_number: int | None = None
) -> None:
    teams = list(enumerate(state.teams, start=1))
    if team_number is not None:
        teams = [(n, t) for n, t in teams if n == team_number]
        if not teams:
            print(f"❌ Team number '{team_number}' is out of range.")
            return

    for number, team in teams:
        print(f"\n  Team {number}: {team.name}")
        for line in format_squad_lines_from_state(state, team, indent="    "):
            print(line)
        yellows, sent_off = team_disciplinary_summary(team, state)
        print(f"    Totals: 🟨 {yellows} | 🟥 {sent_off}")
