import pytest

from src.core.contestant.models import IndividualPlayer, Team
from src.core.sport.registered_sport import RegisteredSport
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.darts_sport_factory import DartsSportFactory
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.sports.football.football_sport_factory import FootballSportFactory


def test_register_sport() -> None:
    engine = SportsSystemEngine()
    engine.register_sport(DARTS_SPORT, DartsSportFactory(), DartsConsoleAdapter())

    sports = engine.get_available_sports()
    assert len(sports) == 1
    assert isinstance(sports[0], RegisteredSport)
    assert sports[0].descriptor == DARTS_SPORT
    assert engine.get_factory("darts") is not None
    assert engine.get_adapter("darts") is not None


def test_register_sport_rejects_mismatched_descriptor() -> None:
    engine = SportsSystemEngine()
    with pytest.raises(ValueError, match="does not match"):
        engine.register_sport(
            FOOTBALL_SPORT, FootballSportFactory(), DartsConsoleAdapter()
        )


def test_darts_factory_create_contest() -> None:
    factory = DartsSportFactory()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    match = factory.create_contest([p1, p2], DartsMatchConfig(starting_score=301))
    assert match.current_state.starting_score == 301


def test_football_factory_create_contest() -> None:
    factory = FootballSportFactory()
    home = Team("Home", "home")
    away = Team("Away", "away")
    match = factory.create_contest([home, away], FootballMatchConfig())
    assert len(match.contestants) == 2
