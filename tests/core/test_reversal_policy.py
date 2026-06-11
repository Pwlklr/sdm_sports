from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command
from src.core.contest.event import Event, EventReversed
from src.core.contest.rule_set import RuleSet
from tests.core.contest_test_support import MinimalContestState, make_contest


@dataclass(frozen=True, kw_only=True)
class Fact(Event):
    pass


@dataclass(frozen=True, kw_only=True)
class Noop(Command):
    pass


class _RuleSet(RuleSet):
    def decide_noop(self, command: Noop, state: MinimalContestState) -> list[Event]:
        return []

    command_handlers = {Noop: decide_noop}
    reaction_handlers = {}


def _contest_with_history(history: list[Event]):
    contest = make_contest(MinimalContestState([]), _RuleSet())
    contest._history = list(history)
    return contest


def test_withdrawn_event_ids_includes_caused_by_descendants() -> None:
    parent = Fact(event_id="p")
    child = Fact(event_id="c", caused_by="p")
    grandchild = Fact(event_id="g", caused_by="c")
    contest = _contest_with_history(
        [
            parent,
            child,
            grandchild,
            EventReversed(target_event_id="p", reason="test"),
        ]
    )

    assert contest._get_withdrawn_event_ids() == {"p", "c", "g"}


def test_effective_domain_events_skips_markers_and_withdrawn() -> None:
    kept = Fact(event_id="kept")
    removed = Fact(event_id="removed")
    contest = _contest_with_history(
        [
            kept,
            removed,
            EventReversed(target_event_id="removed", reason="test"),
        ]
    )

    assert contest._effective_domain_events() == [kept]
