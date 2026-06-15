from src.core.contestant.models import IndividualPlayer, Team
from src.console.tournament_view import schedule_view
from src.core.tournament.draw import RoundRobinDrawStrategy
from src.core.tournament.phase import GroupStagePhase
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT


def test_schedule_view_shows_home_away_labels() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    phase = GroupStagePhase("Group", RoundRobinDrawStrategy())
    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], FootballMatchConfig())
    phase.add_contest(match)

    lines = schedule_view(phase)
    assert "dom" in lines[0]
    assert "wyjazd" in lines[0]
    assert "Home" in lines[0]
