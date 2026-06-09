import pytest
from dataclasses import dataclass

from src.core.contest.command import Command
from src.core.contest import Contest
from src.core.contest.event import Event
from src.core.contest.contest_state import ContestState
from src.core.contestant import IndividualPlayer
from src.core.contest.rule_set import RuleSet
from src.core.tournament.tournament_registration import TournamentRegistration
from src.core.tournament.tournament_scheduler import TournamentScheduler
from src.core.tournament.tournament_disciplinary_board import TournamentDisciplinaryBoard
from src.core.tournament.event import (
    RegistrationOpened,
    PlayerRegistered,
    RegistrationClosed,
    MatchScheduled,
)


class DummyState(ContestState):
    def apply(self, fact: Event) -> None:
        pass


@dataclass(frozen=True, kw_only=True)
class DummyCommand(Command):
    pass


class DummyRuleSet(RuleSet):
    def decide_noop(
        self, command: DummyCommand, state: DummyState
    ) -> list[Event]:
        return []

    command_handlers = {DummyCommand: decide_noop}
    reaction_handlers = {}


def test_tournament_registration_lifecycle() -> None:
    reg = TournamentRegistration()
    p1 = IndividualPlayer("P1")

    # Cannot register while closed
    with pytest.raises(ValueError):
        reg.register(p1)

    # Open registration
    events = reg.open_registration()
    assert isinstance(events[0], RegistrationOpened)
    assert reg.is_open is True

    # Register player
    events = reg.register(p1)
    assert isinstance(events[0], PlayerRegistered)
    assert len(reg.registered_contestants) == 1

    # Cannot double register
    with pytest.raises(ValueError):
        reg.register(p1)

    # Close registration
    events = reg.close_registration()
    assert isinstance(events[0], RegistrationClosed)
    assert reg.is_open is False


def test_tournament_scheduler() -> None:
    scheduler = TournamentScheduler()
    match = Contest([], DummyState(), DummyRuleSet())

    events = scheduler.schedule_match(match)
    assert isinstance(events[0], MatchScheduled)
    assert len(scheduler.pending_matches) == 1

    next_match = scheduler.pop_next_match()
    assert next_match == match
    assert len(scheduler.pending_matches) == 0
    assert scheduler.pop_next_match() is None


def test_tournament_disciplinary_board() -> None:
    board = TournamentDisciplinaryBoard()
    p1 = IndividualPlayer("P1")

    board.log_infraction(p1, "Yellow Card")
    board.log_infraction(p1, "Foul")

    assert len(board.records[p1.id]) == 2
    assert board.records[p1.id] == ["Yellow Card", "Foul"]
