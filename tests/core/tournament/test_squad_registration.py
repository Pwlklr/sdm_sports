"""Tournament squad registration and close-registration gates."""

from __future__ import annotations

import pytest

import src.sports.darts.register_tournament  # noqa: F401
import src.sports.football.register_tournament  # noqa: F401

from src.core.contestant.models import IndividualPlayer, Team
from src.core.shared import CommandRejected
from src.core.tournament import Tournament
from src.core.tournament.tournament_entry import TournamentEntry
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT


def _team_with_roster(name: str, team_id: str, count: int) -> Team:
    team = Team(name, team_id)
    for index in range(1, count + 1):
        team.add_player(IndividualPlayer(f"P{index}", f"{team_id}-p{index}"))
    return team


def _football_tournament() -> Tournament:
    return Tournament.from_blueprint(
        "Cup",
        FOOTBALL_SPORT.id,
        "league",
        match_config=FootballMatchConfig(),
    )


def _darts_tournament() -> Tournament:
    return Tournament.from_blueprint(
        "Open",
        DARTS_SPORT.id,
        "league",
        match_config=DartsMatchConfig(),
    )


def test_register_squad_persists_in_state() -> None:
    team = _team_with_roster("Arsenal", "arsenal", 16)
    tournament = _football_tournament()
    tournament.open_registration()
    tournament.register_contestant(team)
    player_ids = tuple(player.id for player in team.roster[:14])
    tournament.register_squad(team.id, player_ids)
    assert tournament.state.squads[team.id] == player_ids


def test_register_squad_rejects_player_outside_roster() -> None:
    team = _team_with_roster("Arsenal", "arsenal", 16)
    tournament = _football_tournament()
    tournament.open_registration()
    tournament.register_contestant(team)
    with pytest.raises(CommandRejected, match="not on team"):
        tournament.register_squad(team.id, ("unknown-player",) * 14)


def test_close_registration_rejects_missing_squad() -> None:
    team = _team_with_roster("Arsenal", "arsenal", 16)
    tournament = _football_tournament()
    tournament.open_registration()
    tournament.register_contestant(team)
    with pytest.raises(CommandRejected, match="no tournament squad"):
        tournament.close_registration()


def test_darts_auto_registers_individual_squad() -> None:
    player = IndividualPlayer("Luke", "luke")
    tournament = _darts_tournament()
    tournament.open_registration()
    tournament.register_contestant(player)
    assert tournament.state.squads[player.id] == (player.id,)


def test_setup_tournament_registers_squads_for_football() -> None:
    from src.core.system.sports_system_engine import SportsSystemEngine

    teams = [_team_with_roster(f"T{i}", f"t{i}", 16) for i in range(3)]
    tournament = _football_tournament()
    engine = SportsSystemEngine()
    entries = [
        TournamentEntry(
            contestant=team,
            player_ids=tuple(player.id for player in team.roster[:14]),
        )
        for team in teams
    ]
    engine.setup_tournament(tournament, entries)
    for team in teams:
        assert len(tournament.state.squads[team.id]) == 14


def test_fixture_passes_eligible_squads_to_contest() -> None:
    teams = [_team_with_roster(f"T{i}", f"t{i}", 16) for i in range(3)]
    tournament = _football_tournament()
    tournament.open_registration()
    for team in teams:
        tournament.register_contestant(team)
        tournament.register_squad(
            team.id, tuple(player.id for player in team.roster[:14])
        )
    tournament.close_registration()
    match = next(iter(tournament.matches.values()))
    eligible = match.current_state.eligible_player_ids
    for team in teams[:2]:
        assert team.id in eligible
        assert len(eligible[team.id]) == 14
