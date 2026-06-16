from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.football_contest_state import FootballContestState
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT


def test_contest_factory_produces_correct_types_from_config() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    config = FootballMatchConfig(players_on_pitch=5, min_players_on_pitch=3)

    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    state = match.current_state

    assert isinstance(state, FootballContestState)
    assert state.config.players_on_pitch == 5
    assert state.config is config
