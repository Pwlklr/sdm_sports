import pytest

from src.core.contestant import IndividualPlayer
from src.sports.darts.contest.events import MatchStarted
from src.sports.darts.contest.darts_contest_state import DartsContestState


def test_state_requires_players() -> None:
    with pytest.raises(ValueError):
        DartsContestState([])


def test_apply_match_started() -> None:
    p1 = IndividualPlayer("P1", "p1")
    state = DartsContestState([p1])
    state.apply(MatchStarted())
    assert state.match_started is True
    assert state.current_turn is not None
