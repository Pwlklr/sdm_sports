from __future__ import annotations

from typing import Any, List

from src.core.contest import Contest, ContestFactory
from src.core.contestant.models import Contestant
from src.core.sport.console_adapter import ConsoleAdapter


def create_console_contest(
    sport_id: str,
    adapter: ConsoleAdapter,
    contestants: List[Contestant],
    config: Any,
    **options: Any,
) -> Contest:
    """Assemble a contest via ContestFactory and attach the console view."""
    contest = ContestFactory.create(sport_id, contestants, config, **options)
    adapter.attach_view(contest)
    return contest
