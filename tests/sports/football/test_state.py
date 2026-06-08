import pytest

from src.core.contestant import Team
from src.sports.football.config import FootballMatchConfig
from src.sports.football.entities import PeriodKind
from src.sports.football.state import FootballContestState


def _state() -> FootballContestState:
    home = Team("Home", "home")
    away = Team("Away", "away")
    return FootballContestState([home, away], config=FootballMatchConfig())


def test_requires_two_sides() -> None:
    with pytest.raises(ValueError):
        FootballContestState([Team("Solo", "solo")])


def test_opponent_resolution() -> None:
    state = _state()
    home, away = state.teams
    assert state.opponent_of(home) == away
    assert state.opponent_of(away) == home


def test_ensure_match_started_is_idempotent() -> None:
    state = _state()
    state.ensure_match_started()
    state.ensure_match_started()
    assert state.count_periods(PeriodKind.REGULAR) == 1


def test_leading_team() -> None:
    state = _state()
    home, away = state.teams
    assert state.leading_team() is None
    state.scores[home.id] = 2
    assert state.leading_team() == home


def test_penalty_shootout_sudden_death() -> None:
    state = _state()
    home, away = state.teams
    state.penalty_shootout_rounds = 3

    # 3-3 after the regulation rounds -> no winner yet
    state.penalty_attempts = {home.id: 3, away.id: 3}
    state.penalty_scores = {home.id: 3, away.id: 3}
    assert state.penalty_shootout_winner() is None

    # Sudden death: home scores 4th, away misses
    state.penalty_attempts = {home.id: 4, away.id: 4}
    state.penalty_scores = {home.id: 4, away.id: 3}
    assert state.penalty_shootout_winner() == home
