from dataclasses import dataclass

from src.core.contest import Contest
from src.core.contest.command import Command
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event
from src.core.contest.rule_set import RuleSet
from src.core.contestant.models import IndividualPlayer
from src.core.tournament import Tournament
from src.core.tournament.draw import RoundRobinDrawStrategy
from src.core.tournament.event import PhaseCompleted
from src.core.tournament.phase import GroupStagePhase


@dataclass(frozen=True, kw_only=True)
class EndCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class EndFact(Event):
    pass


class DummyState(ContestState):
    def apply(self, fact: Event) -> None:
        if isinstance(fact, EndFact):
            self.is_completed = True


class DummyRuleSet(RuleSet):
    def decide_end(self, command: EndCommand, state: DummyState) -> list[Event]:
        return [EndFact()]

    command_handlers = {EndCommand: decide_end}
    reaction_handlers = {}


def test_policy_advances_phase_when_complete() -> None:
    p1 = IndividualPlayer("P1", "p1")
    p2 = IndividualPlayer("P2", "p2")
    tournament = Tournament("Cup", "t1")
    phase = GroupStagePhase("Group", RoundRobinDrawStrategy())
    tournament.add_phase(phase)
    phase.initialize_standings([p1, p2])

    match = Contest([p1, p2], DummyState(), DummyRuleSet())
    phase.add_contest(match)
    match.handle(EndCommand())

    tournament.complete_match(match)

    assert phase.completed_contests == 1
    assert any(isinstance(e, PhaseCompleted) for e in tournament.history)
    assert tournament.is_completed
    assert tournament.current_phase_idx == 1


def test_player_registered_updates_contestants() -> None:
    tournament = Tournament("Cup", "t2")
    tournament.add_phase(GroupStagePhase("Group", RoundRobinDrawStrategy()))
    tournament.open_registration()
    tournament.register_player(IndividualPlayer("P1", "p1"))
    assert any(c.id == "p1" for c in tournament.contestants)
