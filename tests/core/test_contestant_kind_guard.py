"""Tests for ContestFactory contestant_kind validation."""

import pytest

from src.core.contest.contest_factory import ContestFactory
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT


def test_football_rejects_individual_player_contestant() -> None:
    player = IndividualPlayer("Solo", "solo")
    with pytest.raises(ValueError, match="Team"):
        ContestFactory.create(FOOTBALL_SPORT.id, [player], FootballMatchConfig())


def test_darts_rejects_team_contestant() -> None:
    team = Team("Some Team", "t1")
    with pytest.raises(ValueError, match="IndividualPlayer"):
        ContestFactory.create(DARTS_SPORT.id, [team, team], DartsMatchConfig())


def test_football_accepts_team_contestants() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P", "p1"))
    match = ContestFactory.create(
        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig()
    )
    assert match is not None


def test_darts_accepts_individual_player_contestants() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())
    assert match is not None


def test_factory_rejects_empty_contestant_list() -> None:
    with pytest.raises(ValueError, match="At least one"):
        ContestFactory.create(FOOTBALL_SPORT.id, [], FootballMatchConfig())
