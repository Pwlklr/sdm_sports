import pytest

from src.core.sport.sport_plugin import SportPlugin
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.darts.plugin import DARTS_PLUGIN
from src.sports.football.football_sport_factory import FootballSportFactory
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.sports.football.plugin import FOOTBALL_PLUGIN


def test_engine_registers_plugins_from_constructor() -> None:
    engine = SportsSystemEngine(sports=[DARTS_PLUGIN, FOOTBALL_PLUGIN])

    ids = {sport.descriptor.id for sport in engine.get_available_sports()}
    assert ids == {DARTS_SPORT.id, FOOTBALL_SPORT.id}
    assert engine.get_factory(DARTS_SPORT.id) is not None
    assert engine.get_adapter(FOOTBALL_SPORT.id) is not None


def test_sport_plugin_rejects_mismatched_adapter() -> None:
    with pytest.raises(ValueError, match="does not match"):
        SportPlugin(
            descriptor=FOOTBALL_SPORT,
            factory=FootballSportFactory(),
            adapter=DartsConsoleAdapter(),
        )


def test_engine_default_has_no_sports() -> None:
    engine = SportsSystemEngine()
    assert engine.get_available_sports() == []
