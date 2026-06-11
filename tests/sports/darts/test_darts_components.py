from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_rule_set import DartsRuleSet
from src.sports.darts.descriptor import DARTS_SPORT


def test_contest_factory_pairs_state_and_ruleset_from_same_config() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    config = DartsMatchConfig(starting_score=301)

    match = ContestFactory.create(DARTS_SPORT.id, players, config)
    state = match.current_state
    ruleset = match._ruleset

    assert isinstance(state, DartsContestState)
    assert isinstance(ruleset, DartsRuleSet)
    assert state.config.starting_score == 301
    assert ruleset._config.starting_score == 301
