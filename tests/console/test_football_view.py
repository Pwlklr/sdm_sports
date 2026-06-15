import pytest
from dataclasses import replace
from unittest.mock import MagicMock

from src.core.contest import Contest
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.player_stats import FootballPlayerStats
from src.sports.football.contest.state import create_football_contest_state
from src.sports.football.console.football_console_view import FootballConsoleView


def test_football_scoreboard_shows_player_cards(
    capsys: pytest.CaptureFixture[str],
) -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Saka"))
    home.add_player(IndividualPlayer("Odegaard"))
    state = create_football_contest_state([home, away], FootballMatchConfig())
    stats = dict(state.player_stats)
    stats[home.roster[0].id] = FootballPlayerStats(
        player_id=home.roster[0].id, yellow_cards=1
    )
    stats[home.roster[1].id] = FootballPlayerStats(
        player_id=home.roster[1].id, dismissed=True
    )
    state = replace(state, player_stats=stats)

    mock_contest = MagicMock(spec=Contest)
    mock_contest.current_state = state

    FootballConsoleView().update(mock_contest, None)

    captured = capsys.readouterr()
    assert "🟨×1" in captured.out
    assert "🟥" in captured.out
    assert "Saka" in captured.out
