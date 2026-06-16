"""Tests for Contest reversal logic: withdrawn-event cascade and effective-event view.

All assertions use the public API (contest.history, contest.handle) without
touching private fields directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command, ReverseDecision
from src.core.contest.event import Event, EventReversed, ProjectionEvent
from src.core.contest.rule_set import RuleSet
from tests.core.contest_test_support import MinimalContestState, make_contest


@dataclass(frozen=True, kw_only=True)
class Fact(ProjectionEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class DoSomething(Command):
    pass


class _RuleSet(RuleSet):
    def decide_do_something(
        self, command: DoSomething, state: MinimalContestState, history: list[Event]
    ) -> list[Event]:
        return [Fact()]

    command_handlers = {DoSomething: decide_do_something}
    reaction_handlers = {}


def test_reversal_records_event_reversed_marker() -> None:
    """Reversing an event appends an EventReversed entry to history."""
    contest = make_contest(MinimalContestState([]), _RuleSet())
    contest.handle(DoSomething())
    facts = [e for e in contest.history if isinstance(e, Fact)]
    assert len(facts) == 1

    contest.handle(ReverseDecision(target_event_id=facts[0].event_id, reason="undo"))

    reversals = [e for e in contest.history if isinstance(e, EventReversed)]
    assert len(reversals) == 1
    assert reversals[0].target_event_id == facts[0].event_id


def test_multiple_reversals_accumulate() -> None:
    """Each ReverseDecision adds a separate EventReversed — history is append-only."""
    contest = make_contest(MinimalContestState([]), _RuleSet())
    contest.handle(DoSomething())
    contest.handle(DoSomething())
    facts = [e for e in contest.history if isinstance(e, Fact)]
    assert len(facts) == 2

    for fact in facts:
        contest.handle(ReverseDecision(target_event_id=fact.event_id, reason="undo"))

    reversals = [e for e in contest.history if isinstance(e, EventReversed)]
    assert len(reversals) == 2


def test_history_is_append_only_after_reversal() -> None:
    """No event is ever removed; the log only grows."""
    contest = make_contest(MinimalContestState([]), _RuleSet())
    contest.handle(DoSomething())
    length_after_command = len(contest.history)
    fact_id = [e for e in contest.history if isinstance(e, Fact)][0].event_id

    contest.handle(ReverseDecision(target_event_id=fact_id, reason="undo"))

    assert len(contest.history) == length_after_command + 1


def test_reversal_of_unknown_event_is_rejected() -> None:
    """Reversing an event ID not in history raises ValueError."""
    import pytest

    contest = make_contest(MinimalContestState([]), _RuleSet())
    with pytest.raises(ValueError, match="not part of this contest history"):
        contest.handle(ReverseDecision(target_event_id="nonexistent", reason="oops"))
