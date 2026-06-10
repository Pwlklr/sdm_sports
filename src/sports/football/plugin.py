from __future__ import annotations

from src.core.sport.sport_plugin import SportPlugin
from src.sports.football.adapter import FootballConsoleAdapter
from src.sports.football.football_sport_factory import FootballSportFactory
from src.sports.football.descriptor import FOOTBALL_SPORT

FOOTBALL_PLUGIN = SportPlugin(
    descriptor=FOOTBALL_SPORT,
    factory=FootballSportFactory(),
    adapter=FootballConsoleAdapter(),
)
