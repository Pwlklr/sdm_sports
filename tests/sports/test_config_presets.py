from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.football.contest.football_match_config import FootballMatchConfig


def test_football_presets() -> None:
    assert FootballMatchConfig.fifa().allow_draw is False
    assert FootballMatchConfig.league().allow_draw is True
    assert FootballMatchConfig.league().extra_time_halves == 0
    assert FootballMatchConfig.cup().golden_goal is True


def test_darts_presets() -> None:
    assert DartsMatchConfig.standard_501().starting_score == 501
    assert DartsMatchConfig.quick_301().starting_score == 301
    assert DartsMatchConfig.quick_301().out_multiplier == 1
