from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command
from src.core.contest import Contest
from src.core.contest.result import Result
from tests.core.contest_test_support import EmptyResult, StatefulContestState, make_contest
from src.core.contest.event import Event
from src.core.contestant import Contestant
from src.core.contest.rule_set import RuleSet
from src.core.tournament.phase import DrawStrategy, TournamentPhase


class DummyContestant(Contestant):
    def __init__(self, name: str, contestant_id: str) -> None:
        self._name = name
        self._id = contestant_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def display_name(self) -> str:
        return self._name


@dataclass(frozen=True, kw_only=True)
class EndCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class EndFact(Event):
    pass


class DummyState(StatefulContestState):
    def apply(self, fact: Event) -> None:
        if isinstance(fact, EndFact):
            self.is_final = True

    def reset(self) -> DummyState:
        return DummyState(self.contestants)

    def build_result(self) -> Result:
        return EmptyResult()


class DummyRuleSet(RuleSet):
    def decide_end(self, command: EndCommand, state: DummyState) -> list[Event]:
        return [EndFact()]

    command_handlers = {EndCommand: decide_end}
    reaction_handlers = {}


class DummyDrawStrategy(DrawStrategy):
    def generate_draw(
        self, contestants: list[Contestant]
    ) -> list[tuple[Contestant, Contestant]]:
        return []


class DummyPhase(TournamentPhase):
    def _apply_result(self, contest: Contest) -> None:
        pass

    def get_qualifiers(self) -> list[Contestant]:
        return []


def test_tournament_phase_observes_contest_completion() -> None:
    team_a = DummyContestant(name="Team A", contestant_id="T1")
    team_b = DummyContestant(name="Team B", contestant_id="T2")

    contest = make_contest(
        DummyState([team_a, team_b]), DummyRuleSet(), contest_id="C1"
    )
    phase = DummyPhase("Phase-1", DummyDrawStrategy())

    phase.add_contest(contest)

    assert phase.completed_contests == 0

    contest.handle(EndCommand())

    assert phase.completed_contests == 1
