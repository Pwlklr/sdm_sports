from __future__ import annotations

from typing import Any, List

from src.core.contest import Contest
from src.core.contestant.models import Contestant
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.sport_factory import SportFactory


def create_console_contest(
    factory: SportFactory,
    adapter: ConsoleAdapter,
    contestants: List[Contestant],
    config: Any,
) -> Contest:
    """Assemble a contest via the factory and attach the console view."""
    contest = factory.create_contest(contestants, config)
    adapter.attach_view(contest)
    return contest
