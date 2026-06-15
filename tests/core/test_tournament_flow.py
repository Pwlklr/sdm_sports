from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command
from tests.core.contest_test_support import StatefulContestState, make_contest
from src.core.contest.event import Event
from src.core.contestant import IndividualPlayer
from src.core.tournament.draw import RoundRobinDrawStrategy
from src.core.contest.rule_set import RuleSet
from src.core.tournament import Tournament
from src.core.tournament.event import MatchCompleted, MatchScheduled
from src.core.tournament.phase import GroupStagePhase
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT


@dataclass(frozen=True, kw_only=True)
class EndCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class EndFact(Event):
    pass


class DummyState(StatefulContestState):
    def apply(self, fact: Event) -> DummyState:
        if isinstance(fact, EndFact):
            finished = DummyState(self.contestants)
            finished._finished = True
            return finished
        return DummyState(self.contestants)

    def reset(self) -> DummyState:
        return DummyState(self.contestants)


class DummyRuleSet(RuleSet):
    def decide_end(self, command: EndCommand, state: DummyState) -> list[Event]:
        return [EndFact()]

    command_handlers = {EndCommand: decide_end}
    reaction_handlers = {}


def test_tournament_schedules_matches_on_registration_close() -> None:
    config = DartsMatchConfig()
    players = [
        IndividualPlayer("P1", "p1"),
        IndividualPlayer("P2", "p2"),
        IndividualPlayer("P3", "p3"),
    ]

    tournament = Tournament("Test Cup", "t1")
    tournament.add_phase(GroupStagePhase("Group", RoundRobinDrawStrategy()))
    tournament.open_registration()
    for player in players:
        tournament.register_player(player)

    events = tournament.close_registration(DARTS_SPORT.id, config)
    scheduled = [event for event in events if isinstance(event, MatchScheduled)]

    assert len(scheduled) == 3
    assert len(tournament.scheduler.pending_matches) == 3


def test_tournament_records_match_completion() -> None:
    p1 = IndividualPlayer("P1", "p1")
    p2 = IndividualPlayer("P2", "p2")

    tournament = Tournament("Final", "t2")
    phase = GroupStagePhase("Group", RoundRobinDrawStrategy())
    tournament.add_phase(phase)

    match = make_contest(DummyState([p1, p2]), DummyRuleSet())
    phase.add_contest(match)
    match.handle(EndCommand())
    tournament.complete_match(match)

    assert phase.completed_contests == 1
    assert any(isinstance(event, MatchCompleted) for event in tournament.history)
