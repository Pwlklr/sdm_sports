"""Shared pytest fixtures for all sports tests.

These fixtures provide pre-built Contest objects ready for domain testing,
removing the boilerplate from individual test files.
"""

from __future__ import annotations

import pytest

from src.core.contest.contest import Contest
from src.core.contest.contest_factory import ContestFactory
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT

# ---------------------------------------------------------------------------
# Contestant helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def two_darts_players() -> tuple[IndividualPlayer, IndividualPlayer]:
    return IndividualPlayer("Player A", "p_a"), IndividualPlayer("Player B", "p_b")


@pytest.fixture
def two_football_teams() -> tuple[Team, Team]:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "p9"))
    away.add_player(IndividualPlayer("Keeper", "gk"))
    return home, away


@pytest.fixture
def football_config() -> FootballMatchConfig:
    return FootballMatchConfig(
        allow_draw=True,
        players_on_pitch=1,
        min_players_on_pitch=1,
    )


# ---------------------------------------------------------------------------
# Raw (not-yet-started) contest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def darts_match(two_darts_players) -> Contest:
    """A 501 darts match, not yet started."""
    p1, p2 = two_darts_players
    return ContestFactory.create(DARTS_SPORT.id, [p1, p2], DartsMatchConfig())


@pytest.fixture
def football_match(two_football_teams, football_config) -> Contest:
    """A standard football match (draws allowed), not yet started."""
    home, away = two_football_teams
    return ContestFactory.create(FOOTBALL_SPORT.id, [home, away], football_config)


@pytest.fixture
def football_knockout_match(two_football_teams, football_config) -> Contest:
    """A knockout football match (no draws, goes to extra time then penalties)."""
    home, away = two_football_teams
    config = FootballMatchConfig(
        allow_draw=False,
        extra_time_halves=2,
        penalty_shootout_rounds=5,
        players_on_pitch=football_config.players_on_pitch,
        min_players_on_pitch=football_config.min_players_on_pitch,
    )
    return ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)


# ---------------------------------------------------------------------------
# Started contest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def started_darts_match(darts_match) -> Contest:
    from src.sports.darts.contest.commands import StartMatch

    darts_match.handle(StartMatch())
    return darts_match


@pytest.fixture
def started_football_match(football_match) -> Contest:
    from src.sports.football.contest.commands import StartMatch
    from tests.sports.football.lineup_helpers import submit_all_lineups

    football_match.handle(StartMatch())
    submit_all_lineups(football_match)
    return football_match


# ---------------------------------------------------------------------------
# Finished contest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def finished_football_match(started_football_match) -> Contest:
    """A finished football match (home wins 1-0)."""
    from src.sports.football.contest.commands import EndPeriod, ScoreGoal

    started_football_match.handle(ScoreGoal(team_index=0, minute=10))
    started_football_match.handle(EndPeriod())
    started_football_match.handle(EndPeriod())
    return started_football_match
