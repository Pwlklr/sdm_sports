from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.contest.match_metrics_reader import MatchMetricsReader
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor


@dataclass(frozen=True)
class RegisteredSport:
    descriptor: SportDescriptor
    adapter: Optional[ConsoleAdapter] = None
    match_metrics_reader: Optional[MatchMetricsReader] = None
