from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.core.contest.command import Command
from tests.core.contest_test_support import StatefulContestState
from src.core.contest.result import Result
from src.core.contest.event import Event
from src.core.contest.rule_set import RuleSet


@dataclass(frozen=True, kw_only=True)
class CmdA(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class CmdB(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class FactA(Event):
    pass


class _State(StatefulContestState):
    def apply(self, fact: Event) -> None:
        pass

    def reset(self) -> _State:
        return _State(self.contestants)

    def build_result(self) -> Result:
        from tests.core.contest_test_support import EmptyResult

        return EmptyResult()


class MixinA:
    def decide_a(self, command: CmdA, state: _State) -> list[Event]:
        return [FactA()]

    _own_command_handlers = {CmdA: decide_a}


class MixinB:
    def decide_b(self, command: CmdB, state: _State) -> list[Event]:
        return []

    _own_command_handlers = {CmdB: decide_b}


def test_handlers_merge_across_mixins() -> None:
    class Composed(MixinA, MixinB, RuleSet):
        pass

    assert set(Composed.command_handlers) == {CmdA, CmdB}
    ruleset = Composed()
    assert len(ruleset.decide(CmdA(), _State())) == 1
    assert ruleset.decide(CmdB(), _State()) == []


def test_conflicting_handlers_raise() -> None:
    class MixinC:
        def decide_a_other(self, command: CmdA, state: _State) -> list[Event]:
            return []

        _own_command_handlers = {CmdA: decide_a_other}

    with pytest.raises(TypeError, match="conflicting handler"):

        class Broken(MixinA, MixinC, RuleSet):
            pass
