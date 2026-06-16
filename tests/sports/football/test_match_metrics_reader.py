from dataclasses import replace

from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result_builder import FootballResultBuilder
from src.sports.football.contest.match_metrics_reader import FootballMatchMetricsReader
from src.sports.football.contest.player_stats import FootballPlayerStats
from src.sports.football.contest.football_contest_state import create_football_contest_state
from src.core.contestant.models import IndividualPlayer, Team


def test_match_metrics_reader_top_scorers() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P1", "p1"))
    state = create_football_contest_state([home, away], FootballMatchConfig())
    stats = dict(state.player_stats)
    stats["p1"] = FootballPlayerStats(player_id="p1", goals=2)
    state = replace(state, player_stats=stats, is_finished=True)

    result = FootballResultBuilder(config=FootballMatchConfig()).build(state)
    scorers = FootballMatchMetricsReader().top_scorers(result)

    assert scorers == [("p1", 2)]
