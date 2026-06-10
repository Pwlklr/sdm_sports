from src.core.contestant.models import IndividualPlayer, Team
from src.console.tournament_view import schedule_view
from src.core.tournament.draw import RoundRobinDrawStrategy
from src.core.tournament.phase import GroupStagePhase
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.football_sport_factory import FootballSportFactory


def test_contest_exposes_home_and_away() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    match = FootballSportFactory().create_contest([home, away], FootballMatchConfig())
    assert match.home is home
    assert match.away is away


def test_schedule_view_shows_home_away_labels() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    phase = GroupStagePhase("Group", RoundRobinDrawStrategy())
    match = FootballSportFactory().create_contest([home, away], FootballMatchConfig())
    phase.add_contest(match)

    lines = schedule_view(phase)
    assert "dom" in lines[0]
    assert "wyjazd" in lines[0]
    assert "Home" in lines[0]
