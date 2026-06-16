from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from src.core.contest.event import Event


@dataclass(frozen=True)
class ReversalOption:
    number: int
    event_id: str
    label: str


def build_numbered_catalog(
    events: Sequence[Event],
    label_for: Callable[[Event], str],
) -> list[ReversalOption]:
    return [
        ReversalOption(number=index, event_id=event.event_id, label=label_for(event))
        for index, event in enumerate(events, start=1)
    ]


def format_reversal_menu(
    catalog: list[ReversalOption],
    *,
    title: str,
    usage: str,
    empty_label: str,
) -> list[str]:
    """Render a reversal menu as plain lines, leaving I/O to the caller."""
    lines = [f"\n--- {title} ---"]
    if not catalog:
        lines.append(f"  {empty_label}")
    else:
        lines.extend(f"  {option.number}. {option.label}" for option in catalog)
    lines.append(f"  ({usage})")
    return lines


def parse_reversal_choice(parts: list[str]) -> int | None:
    if len(parts) < 2:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def resolve_catalog_choice(
    catalog: list[ReversalOption], choice: int
) -> ReversalOption | None:
    return next((option for option in catalog if option.number == choice), None)
