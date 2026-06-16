from __future__ import annotations

from src.core.contestant.models import IndividualPlayer, Team


def resolve_roster_player_by_number(team: Team, player_number: int) -> IndividualPlayer:
    return team.roster[player_number - 1]


def player_on_team(team: Team, player_id: str) -> bool:
    return any(player.id == player_id for player in team.roster)


def match_clock_limit(state: object) -> int:
    from src.sports.football.contest.football_contest_state import FootballContestState

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
    from src.sports.football.contest.football_contest_state import FootballContestState

    if player_id is None or not isinstance(state, FootballContestState):
        return ""
    for team in state.teams:
        if not isinstance(team, Team):
            continue
        for player in team.roster:
            if player.id == player_id:
                return player.name
    return "?"
