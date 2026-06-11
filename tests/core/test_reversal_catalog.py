from __future__ import annotations

from dataclasses import dataclass

from src.core.console.reversal_catalog import (
    build_numbered_catalog,
    parse_reversal_choice,
    resolve_catalog_choice,
)
from src.core.contest.event import Event


@dataclass(frozen=True, kw_only=True)
class SampleEvent(Event):
    tag: str = ""


def test_build_numbered_catalog_starts_at_one() -> None:
    events = [
        SampleEvent(event_id="a", tag="first"),
        SampleEvent(event_id="b", tag="second"),
    ]
    catalog = build_numbered_catalog(events, lambda event: event.tag)

    assert [(item.number, item.event_id, item.label) for item in catalog] == [
        (1, "a", "first"),
        (2, "b", "second"),
    ]


def test_resolve_catalog_choice_by_number() -> None:
    catalog = build_numbered_catalog(
        [SampleEvent(event_id="x")],
        lambda _event: "label",
    )
    assert resolve_catalog_choice(catalog, 1) is not None
    assert resolve_catalog_choice(catalog, 1).event_id == "x"
    assert resolve_catalog_choice(catalog, 9) is None


def test_parse_reversal_choice() -> None:
    assert parse_reversal_choice(["reverse", "3"]) == 3
    assert parse_reversal_choice(["reverse"]) is None
    assert parse_reversal_choice(["reverse", "x"]) is None
