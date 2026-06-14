from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor


@dataclass(frozen=True)
class RegisteredSport:
    descriptor: SportDescriptor
    adapter: ConsoleAdapter
    match_metrics_reader: Any = None
