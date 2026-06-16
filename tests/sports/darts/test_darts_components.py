from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT


def test_contest_factory_produces_correct_types_from_config() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    config = DartsMatchConfig(starting_score=301)

    match = ContestFactory.create(DARTS_SPORT.id, players, config)
    state = match.current_state

    assert isinstance(state, DartsContestState)
    assert state.config.starting_score == 301
