"""Tests for SportsSystemEngine sport registration."""

import pytest

from src.core.sport.registered_sport import RegisteredSport
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.descriptor import DARTS_SPORT
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
