from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from src.core.contest.contest import Contest
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event
from src.core.contest.result_builder import ResultBuilder
from src.core.contest.rule_set import RuleSet
from src.core.contestant.models import Contestant, IndividualPlayer, Team
from src.core.sport.sport_descriptor import ContestantKind, SportDescriptor


@dataclass(frozen=True, kw_only=True)
class ContestAssembly:
    state: ContestState
    ruleset: RuleSet
    result_builder: ResultBuilder


ContestBuilder = Callable[..., ContestAssembly]


class ContestFactory:
    """Creates a Contest for a registered sport (state + ruleset + result_builder)."""

    _builders: dict[str, ContestBuilder] = {}
    _descriptors: dict[str, SportDescriptor] = {}

    @classmethod
    def register(
        cls,
        sport_id: str,
        builder: ContestBuilder,
        descriptor: SportDescriptor | None = None,
    ) -> None:
        if sport_id in cls._builders:
            raise ValueError(f"Contest builder already registered for '{sport_id}'")
        cls._builders[sport_id] = builder
        if descriptor is not None:
            cls._descriptors[sport_id] = descriptor

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
        descriptor = cls._descriptors.get(sport_id)
        if descriptor is not None:
            _validate_contestant_kind(contestants, descriptor.contestant_kind)
        return builder(contestants, config, **options)


def _validate_contestant_kind(
    contestants: list[Contestant], kind: ContestantKind
) -> None:
    """Enforce that all contestants match the sport's declared contestant kind."""
    if not contestants:
        raise ValueError("At least one contestant is required.")
    if kind == "team":
        bad = [c for c in contestants if not isinstance(c, Team)]
        if bad:
            raise ValueError(
                f"Sport requires Team contestants; got: "
                f"{[type(c).__name__ for c in bad]}"
            )
    elif kind == "individual":
        bad = [c for c in contestants if not isinstance(c, IndividualPlayer)]
        if bad:
            raise ValueError(
                f"Sport requires IndividualPlayer contestants; got: "
                f"{[type(c).__name__ for c in bad]}"
            )
