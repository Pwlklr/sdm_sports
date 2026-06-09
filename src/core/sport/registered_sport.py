from __future__ import annotations

from dataclasses import dataclass

from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor
from src.core.sport.sport_factory import SportFactory


@dataclass(frozen=True)
class RegisteredSport:
    descriptor: SportDescriptor
    factory: SportFactory
    adapter: ConsoleAdapter
