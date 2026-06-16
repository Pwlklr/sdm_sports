"""Football ContestFactory — create and rehydrate contests."""

import pytest

from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import ScoreGoal, StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import FootballResult


def _teams() -> tuple[Team, Team]:
    home, away = Team("Home", "home"), Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    return home, away


def test_create_contest_has_correct_contestants() -> None:
    home, away = _teams()
    match = ContestFactory.create("football", [home, away], FootballMatchConfig())
    assert len(match.contestants) == 2
    assert match.contestants[0] is home


def test_from_events_rehydrates_same_scores() -> None:
    home, away = _teams()
    config = FootballMatchConfig()
    live = ContestFactory.create("football", [home, away], config)
    live.handle(StartMatch())
    live.handle(ScoreGoal(team_index=0, minute=10))

    rehydrated = ContestFactory.from_events(
        "football", [home, away], config, live.history
    )

    assert rehydrated.current_state.scores == live.current_state.scores
    assert rehydrated.current_state.match_started is True
    assert len(rehydrated.history) == len(live.history)


def test_result_type_after_completed_match() -> None:
    from src.sports.football.contest.commands import EndPeriod
    from src.core.tournament.ranking import single_first_place

    home, away = _teams()
    match = ContestFactory.create("football", [home, away], FootballMatchConfig())
    match.handle(StartMatch())
    match.handle(ScoreGoal(team_index=0, minute=10))
    match.handle(EndPeriod())
    match.handle(EndPeriod())

    result = match.get_official_result()
    assert isinstance(result, FootballResult)
    assert single_first_place(result.ranking()) is home


def test_create_rejects_wrong_contestant_kind() -> None:
    p1, p2 = IndividualPlayer("P1"), IndividualPlayer("P2")
    with pytest.raises(ValueError, match="Team"):
        ContestFactory.create("football", [p1, p2], FootballMatchConfig())
