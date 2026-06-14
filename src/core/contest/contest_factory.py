from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from src.core.contest.contest import Contest
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event
from src.core.contest.result_builder import ResultBuilder
from src.core.contest.rule_set import RuleSet
from src.core.contestant.models import Contestant


@dataclass(frozen=True, kw_only=True)
class ContestAssembly:
    state: ContestState
    ruleset: RuleSet
    result_builder: ResultBuilder


ContestBuilder = Callable[..., ContestAssembly]


class ContestFactory:
    """Tworzy Contest dla zarejestrowanego sportu (state + ruleset + result_builder)."""

    _builders: dict[str, ContestBuilder] = {}

    @classmethod
    def register(cls, sport_id: str, builder: ContestBuilder) -> None:
        if sport_id in cls._builders:
            raise ValueError(f"Contest builder already registered for '{sport_id}'")
        cls._builders[sport_id] = builder

    @classmethod
    def create(
        cls,
        sport_id: str,
        contestants: list[Contestant],
        config: Any,
        *,
        contest_id: str | None = None,
        **options: Any,
    ) -> Contest:
        assembly = cls._build(sport_id, contestants, config, **options)
        return Contest(
            assembly.state,
            assembly.ruleset,
            assembly.result_builder,
            contest_id=contest_id,
        )

    @classmethod
    def from_events(
        cls,
        sport_id: str,
        contestants: list[Contestant],
        config: Any,
        events: Iterable[Event],
        *,
        contest_id: str | None = None,
        **options: Any,
    ) -> Contest:
        assembly = cls._build(sport_id, contestants, config, **options)
        return Contest.from_events(
            assembly.state,
            assembly.ruleset,
            assembly.result_builder,
            events,
            contest_id=contest_id,
        )

    @classmethod
    def _build(
        cls,
        sport_id: str,
        contestants: list[Contestant],
        config: Any,
        **options: Any,
    ) -> ContestAssembly:
        builder = cls._builders.get(sport_id)
        if builder is None:
            raise ValueError(f"No contest builder registered for sport '{sport_id}'")
        return builder(contestants, config, **options)
