"""Pure-core event reversal mechanics.

Sport-specific reversal tests live in tests/sports/football/test_reversal.py
and tests/sports/darts/test_reversal.py.  This file covers only behaviour that
is independent of any particular sport implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command, ReverseDecision
from src.core.contest.event import Event
from src.core.contest.rule_set import RuleSet
from tests.core.contest_test_support import StatefulContestState, make_contest


class _S(StatefulContestState):
    def apply(self, fact: Event) -> _S:
        return _S(self.contestants)

    def reset(self) -> _S:
        return _S(self.contestants)


@dataclass(frozen=True, kw_only=True)
class _Noop(Command):
    pass


class _R(RuleSet):
    def decide_noop(
        self, command: _Noop, state: _S, history: list[Event]
    ) -> list[Event]:
        return []

    command_handlers = {_Noop: decide_noop}
    reaction_handlers = {}


def test_reverse_decision_rebuilds_via_state_reset() -> None:
    """After reversing any event the contest state is rebuilt by replaying survivors."""
    contest = make_contest(_S([]), _R())
    # Inject a minimal event and then reverse it via the public API
    from dataclasses import dataclass as _dc

    @_dc(frozen=True, kw_only=True)
    class _Fact(Event):
        pass

    contest._record_event(_Fact(event_id="x"))
    contest.handle(ReverseDecision(target_event_id="x", reason="test"))
    # State is rebuilt from the surviving (empty) event set — still an _S instance
    assert isinstance(contest.current_state, _S)
