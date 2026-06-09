
from src.core.contest import Contest
from src.core.contestant import IndividualPlayer
from src.sports.darts.contest.commands import CallOcheFault, StartMatch, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.darts_sport_factory import DartsSportFactory


def _contest() -> Contest:
    factory = DartsSportFactory()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    return factory.create_contest([p1, p2], DartsMatchConfig())


def test_start_command_kicks_off() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    assert contest.current_state.match_started is True
    assert contest.current_state.current_turn is not None


def test_throw_dart_command() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    contest.handle(ThrowDart(sector=20, multiplier=3))
    assert contest.current_state.scores[contest.contestants[0].id] == 441


def test_oche_fault_command() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    contest.handle(CallOcheFault())
    assert len(contest.current_state.current_turn.throws) == 1
