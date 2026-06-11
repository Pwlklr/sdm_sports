from __future__ import annotations

import src.sports.darts.register_contest  # noqa: F401 — rejestracja w ContestFactory

from src.core.sport.sport_plugin import SportPlugin
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.descriptor import DARTS_SPORT

DARTS_PLUGIN = SportPlugin(
    descriptor=DARTS_SPORT,
    adapter=DartsConsoleAdapter(),
)
