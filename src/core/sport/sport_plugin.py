from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor


@dataclass(frozen=True)
class SportPlugin:
    """Self-contained registration bundle for a sport: descriptor and console adapter."""

    descriptor: SportDescriptor
    adapter: ConsoleAdapter
    match_metrics_reader: Any = None

    def __post_init__(self) -> None:
        if self.adapter.descriptor != self.descriptor:
            raise ValueError(
                f"Adapter descriptor '{self.adapter.descriptor.id}' does not match "
                f"plugin sport '{self.descriptor.id}'."
            )
