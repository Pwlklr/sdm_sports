from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import FootballContestState
from src.sports.football.descriptor import FOOTBALL_SPORT


def test_contest_factory_pairs_state_and_ruleset_from_same_config() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    config = FootballMatchConfig(players_on_pitch=5, min_players_on_pitch=3)

    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    state = match.current_state
    ruleset = match._ruleset

    assert isinstance(state, FootballContestState)
    assert isinstance(ruleset, FootballRuleSet)
    assert state.config.players_on_pitch == 5
    assert ruleset._config.players_on_pitch == 5
    assert state.config is config
    assert ruleset._config is config
