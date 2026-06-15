import pytest

from dataclasses import replace

from src.core.contestant import Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.entities import PeriodKind
from src.sports.football.contest.events import MatchStarted, PeriodStarted
from src.sports.football.contest.state import create_football_contest_state


def _state():
    home = Team("Home", "home")
    away = Team("Away", "away")
    return create_football_contest_state([home, away], FootballMatchConfig())


def test_requires_two_sides() -> None:
    with pytest.raises(ValueError):
        create_football_contest_state([Team("Solo", "solo")], FootballMatchConfig())


def test_opponent_resolution() -> None:
    state = _state()
    home, away = state.teams
    assert state.opponent_of(home) == away
    assert state.opponent_of(away) == home


def test_apply_starts_period() -> None:
    state = _state()
    state = state.apply(MatchStarted())
    state = state.apply(PeriodStarted(kind=PeriodKind.REGULAR, index=0))
    assert state.count_periods(PeriodKind.REGULAR) == 1


def test_leading_team() -> None:
    state = _state()
    home, away = state.teams
    assert state.leading_team() is None
    state = replace(state, scores={home.id: 2, away.id: 0})
    assert state.leading_team() == home
