import pytest



from src.core.contest import ContestFactory

from src.core.contestant.models import IndividualPlayer, Team

from src.core.sport.registered_sport import RegisteredSport

from src.core.system.sports_system_engine import SportsSystemEngine

from src.sports.darts.adapter import DartsConsoleAdapter

from src.sports.darts.contest.darts_match_config import DartsMatchConfig

from src.sports.darts.descriptor import DARTS_SPORT

from src.sports.football.contest.football_match_config import FootballMatchConfig

from src.sports.football.descriptor import FOOTBALL_SPORT





def test_register_sport() -> None:

    engine = SportsSystemEngine()

    engine.register_sport(DARTS_SPORT, DartsConsoleAdapter())



    sports = engine.get_available_sports()

    assert len(sports) == 1

    assert isinstance(sports[0], RegisteredSport)

    assert sports[0].descriptor == DARTS_SPORT

    assert engine.get_adapter("darts") is not None





def test_register_sport_rejects_mismatched_descriptor() -> None:

    engine = SportsSystemEngine()

    with pytest.raises(ValueError, match="does not match"):

        engine.register_sport(FOOTBALL_SPORT, DartsConsoleAdapter())





def test_darts_factory_create_contest() -> None:

    p1 = IndividualPlayer("P1")

    p2 = IndividualPlayer("P2")

    match = ContestFactory.create("darts", [p1, p2], DartsMatchConfig(starting_score=301))

    assert match.current_state.config.starting_score == 301





def test_darts_factory_from_events() -> None:

    p1 = IndividualPlayer("P1")

    p2 = IndividualPlayer("P2")

    config = DartsMatchConfig(starting_score=301)

    live = ContestFactory.create("darts", [p1, p2], config)

    rehydrated = ContestFactory.from_events("darts", [p1, p2], config, live.history)

    assert (
        rehydrated.current_state.config.starting_score
        == live.current_state.config.starting_score
    )





def test_football_factory_create_contest() -> None:

    home = Team("Home", "home")

    away = Team("Away", "away")

    match = ContestFactory.create("football", [home, away], FootballMatchConfig())

    assert len(match.contestants) == 2





def test_football_factory_from_events() -> None:

    home = Team("Home", "home")

    away = Team("Away", "away")

    live = ContestFactory.create("football", [home, away], FootballMatchConfig())

    rehydrated = ContestFactory.from_events(

        "football", [home, away], FootballMatchConfig(), live.history

    )

    assert rehydrated.current_state.scores == live.current_state.scores

