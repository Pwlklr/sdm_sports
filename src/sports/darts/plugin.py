from __future__ import annotations

from src.core.sport.sport_plugin import SportPlugin
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.darts_sport_factory import DartsSportFactory
from src.sports.darts.descriptor import DARTS_SPORT

DARTS_PLUGIN = SportPlugin(
    descriptor=DARTS_SPORT,
    factory=DartsSportFactory(),
    adapter=DartsConsoleAdapter(),
)
