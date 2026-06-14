import pytest

from src.core.contestant import IndividualPlayer
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.events import MatchStarted
from src.sports.darts.contest.darts_contest_state import create_darts_contest_state


def test_state_requires_players() -> None:
    with pytest.raises(ValueError):
        create_darts_contest_state([], DartsMatchConfig())


def test_apply_match_started() -> None:
    p1 = IndividualPlayer("P1", "p1")
    state = create_darts_contest_state([p1], DartsMatchConfig())
    state = state.apply(MatchStarted())
    assert state.match_started is True
    assert state.current_turn is not None
