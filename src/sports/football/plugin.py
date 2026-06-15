from __future__ import annotations

import src.sports.football.register_contest  # noqa: F401 — rejestracja w ContestFactory

from src.core.sport.sport_plugin import SportPlugin
from src.sports.football.adapter import FootballConsoleAdapter
from src.sports.football.contest.match_metrics_reader import FootballMatchMetricsReader
from src.sports.football.descriptor import FOOTBALL_SPORT

FOOTBALL_PLUGIN = SportPlugin(
    descriptor=FOOTBALL_SPORT,
    adapter=FootballConsoleAdapter(),
    match_metrics_reader=FootballMatchMetricsReader(),
)
