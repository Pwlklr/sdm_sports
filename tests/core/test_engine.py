from __future__ import annotations

import pytest

from dataclasses import dataclass

from src.core.contest.command import Command
from tests.core.contest_test_support import StatefulContestState, make_contest
from src.core.contest.event import Event
from src.core.system.sports_system_engine import SportsSystemEngine
from src.core.contest.rule_set import RuleSet


@dataclass(frozen=True, kw_only=True)
class DummyCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class DummyFact(Event):
    pass


class DummyState(StatefulContestState):
    def apply(self, fact: Event) -> DummyState:
        return DummyState(self.contestants)

    def reset(self) -> DummyState:
        return DummyState(self.contestants)


class DummyRuleSet(RuleSet):
    def decide_dummy(self, command: DummyCommand, state: DummyState) -> list[Event]:
        return [DummyFact()]

    command_handlers = {DummyCommand: decide_dummy}
    reaction_handlers = {}


def test_engine_player_management() -> None:
    engine = SportsSystemEngine()

    p1 = engine.create_individual_player(
        "Phil Taylor", metadata={"nickname": "The Power"}
    )
    team = engine.create_team("FC Python")

    assert p1.id in engine.global_players
    assert team.id in engine.global_players
    assert engine.global_players[p1.id].name == "Phil Taylor"
    assert engine.global_players[p1.id].metadata["nickname"] == "The Power"
    assert engine.global_players[team.id].name == "FC Python"


def test_engine_tournament_management() -> None:
    engine = SportsSystemEngine()
    t1 = engine.create_tournament("World Championship")

    assert t1.id in engine.tournaments
    assert engine.tournaments[t1.id].name == "World Championship"
    assert t1.registration is not None
    assert t1.scheduler is not None


def test_engine_match_dispatch() -> None:
    engine = SportsSystemEngine()
    match = make_contest(DummyState([]), DummyRuleSet())
    engine.register_active_match(match)

    engine.dispatch_match_command(match.id, DummyCommand())
    assert len(match.history) == 1

    with pytest.raises(ValueError, match="not found in active memory"):
        engine.dispatch_match_command("invalid_match_id", DummyCommand())


def test_engine_archiving() -> None:
    engine = SportsSystemEngine()
    match = make_contest(DummyState([]), DummyRuleSet())
    engine.register_active_match(match)

    engine.archive_match(match.id)

    assert match.id not in engine.active_matches
    assert match.id in engine.archived_matches

    with pytest.raises(ValueError):
        engine.archive_match("invalid_id")
