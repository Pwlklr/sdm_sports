from __future__ import annotations

from dataclasses import dataclass

from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.state import FootballContestState


@dataclass(frozen=True)
class PlayerRosterStatus:
    """Match-time roster row: identity from Team.roster, stats from state.player_stats."""

    player_number: int
    player: IndividualPlayer
    yellow_cards: int
    dismissed: bool

    @property
    def player_id(self) -> str:
        return self.player.id

    @property
    def name(self) -> str:
        return self.player.name


def roster_status_for_team(
    state: FootballContestState, team: Team
) -> list[PlayerRosterStatus]:
    return [
        PlayerRosterStatus(
            player_number=number,
            player=player,
            yellow_cards=state.player_stats[player.id].yellow_cards
            if player.id in state.player_stats
            else 0,
            dismissed=state.player_stats[player.id].dismissed
            if player.id in state.player_stats
            else False,
        )
        for number, player in enumerate(team.roster, start=1)
    ]


def roster_status_for_match(
    state: FootballContestState,
) -> dict[str, list[PlayerRosterStatus]]:
    result: dict[str, list[PlayerRosterStatus]] = {}
    for team in state.teams:
        result[team.id] = roster_status_for_team(state, team)
    return result


def format_player_card_suffix(status: PlayerRosterStatus) -> str:
    if status.dismissed:
        return " 🟥"
    if status.yellow_cards:
        return f" 🟨×{status.yellow_cards}"
    return ""


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


def team_disciplinary_summary(
    team: Team, state: FootballContestState
) -> tuple[int, int]:
    yellows = 0
    sent_off = 0
    for player in team.roster:
        stats = state.player_stats.get(player.id)
        if stats is None:
            continue
        yellows += stats.yellow_cards
        if stats.dismissed:
            sent_off += 1
    return yellows, sent_off


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
