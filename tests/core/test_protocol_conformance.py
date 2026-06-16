from __future__ import annotations

from src.core.contest.contest_state import ContestState
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.darts.contest.darts_contest_state import create_darts_contest_state
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.football.contest.football_contest_state import (
    create_football_contest_state,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from tests.core.contest_test_support import MinimalContestState, StatefulContestState


def test_sport_states_explicitly_implement_contest_state_protocol() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    football_state = create_football_contest_state([home, away], FootballMatchConfig())
    darts_state = create_darts_contest_state(
        [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")],
        DartsMatchConfig(),
    )

    for state in (
        football_state,
        darts_state,
        StatefulContestState(),
        MinimalContestState(),
    ):
        assert isinstance(state, ContestState)
