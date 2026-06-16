from src.sports.football.contest.roster import (
    parse_console_team_number,
    parse_console_player_number,
    format_squad_lines,
    parse_console_minute,
    match_clock_limit,
    player_name_for_id
)
from src.sports.football.contestant.football_team import FootballTeam
from src.core.contestant.models import IndividualPlayer
from src.sports.football.contest.football_contest_state import FootballContestState
from src.core.contestant.models import IndividualPlayer
from src.sports.football.contestant.football_team import FootballTeam


from unittest.mock import MagicMock

def test_format_squad_lines_populated() -> None:
    """Covers the roster iteration when the team is not empty."""
    team = FootballTeam(name="Team A", contestant_id="t1")
    team.add_player(IndividualPlayer(name="Player One", contestant_id="p1"))
    
    lines = format_squad_lines(team, indent="")
    assert "1. Player One" in lines[0]

def test_parse_console_team_number_errors(capsys) -> None:
    assert parse_console_team_number("abc", 2) is None
    assert "Team must be a number" in capsys.readouterr().out
    assert parse_console_team_number("0", 2) is None
    assert "out of range" in capsys.readouterr().out

def test_parse_console_player_number_errors(capsys) -> None:
    team = FootballTeam(name="Team A", contestant_id="t1")
    assert parse_console_player_number("1", team) is None
    assert "has no players" in capsys.readouterr().out
    
    team.add_player(IndividualPlayer(name="P1", contestant_id="p1"))
    assert parse_console_player_number("abc", team) is None
    assert "Player must be a number" in capsys.readouterr().out
    assert parse_console_player_number("2", team) is None
    assert "out of range" in capsys.readouterr().out

def test_format_squad_lines_empty() -> None:
    team = FootballTeam(name="Team A", contestant_id="t1")
    assert "(empty squad)" in format_squad_lines(team)[0]

def test_parse_console_minute_errors(capsys) -> None:
    assert parse_console_minute("abc", 90) is None
    assert "Minute must be a number" in capsys.readouterr().out
    assert parse_console_minute("-5", 90) is None
    assert "cannot be negative" in capsys.readouterr().out
    assert parse_console_minute("95", 90) is None
    assert "exceeds current match clock" in capsys.readouterr().out

def test_match_clock_limit_invalid() -> None:
    assert match_clock_limit(None) == 0

def test_player_name_for_id_invalid() -> None:
    assert player_name_for_id(None, "p1") == ""
    
    mock_state = MagicMock(spec=FootballContestState)
    mock_state.teams = ["not_a_team"] 
    
    assert player_name_for_id(mock_state, "p1") == "?"