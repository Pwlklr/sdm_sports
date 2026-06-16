from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.contest.match_metrics_reader import MatchMetricsReader
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_descriptor import SportDescriptor


@dataclass(frozen=True)
class SportPlugin:
    """Registration bundle for a sport: domain descriptor plus optional console adapter.

    The console adapter is optional so a sport can be registered for headless use
    (tests, services) without depending on console presentation.
    """

    descriptor: SportDescriptor
    adapter: Optional[ConsoleAdapter] = None
    match_metrics_reader: Optional[MatchMetricsReader] = None

    def __post_init__(self) -> None:
        if self.adapter is not None and self.adapter.descriptor != self.descriptor:
            raise ValueError(
                f"Adapter descriptor '{self.adapter.descriptor.id}' does not match "
                f"plugin sport '{self.descriptor.id}'."
            )
