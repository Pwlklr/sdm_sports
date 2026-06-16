from __future__ import annotations

from src.core.contest import Contest
from src.core.contestant.models import Team
from src.sports.football.contest.commands import SubmitLineup
from src.sports.football.contest.football_contest_state import FootballContestState


def submit_all_lineups(contest: Contest) -> None:
    """Submit starting XI + bench for every team using roster order."""
    state = contest.current_state
    if not isinstance(state, FootballContestState):
        raise TypeError("Expected a football contest.")
    for team_index, team in enumerate(state.teams):
        if not isinstance(team, Team):
            continue
        required = state.config.players_on_pitch
        player_ids = [player.id for player in team.roster]
        if len(player_ids) < required:
            starting = tuple(player_ids)
            bench: tuple[str, ...] = ()
        else:
            starting = tuple(player_ids[:required])
            bench = tuple(player_ids[required:])
        contest.handle(
            SubmitLineup(team_index=team_index, starting=starting, bench=bench)
        )
