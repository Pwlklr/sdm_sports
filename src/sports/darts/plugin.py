from __future__ import annotations

import src.sports.darts.register_contest  # noqa: F401 — ContestFactory registration
import src.sports.darts.register_tournament  # noqa: F401 — tournament profile registration

from src.core.sport.sport_plugin import SportPlugin
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.contest.match_metrics_reader import DartsMatchMetricsReader
from src.sports.darts.descriptor import DARTS_SPORT

DARTS_PLUGIN = SportPlugin(
    descriptor=DARTS_SPORT,
    adapter=DartsConsoleAdapter(),
    match_metrics_reader=DartsMatchMetricsReader(),
)
