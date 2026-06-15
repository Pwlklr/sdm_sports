import pytest
from unittest.mock import MagicMock

from src.core.contestant.models import Team, IndividualPlayer
from src.sports.football.console.football_command_parser import parse_football_command
from src.sports.football.contest.commands import (
    StartMatch, EndPeriod, ScoreGoal, CommitFoul, SubmitLineup, SubstitutePlayer, TakePenaltyKick
)
from src.sports.football.contest.state import FootballContestState, MatchPhase


@pytest.fixture
def state():
    s = MagicMock(spec=FootballContestState)
    s.phase = MatchPhase.REGULATION
    
    team1 = Team("Team 1")
    team1.add_player(IndividualPlayer("P1", "p1")) # Numer w rosterze: 1
    team1.add_player(IndividualPlayer("P2", "p2")) # Numer w rosterze: 2

    team2 = Team("Team 2")
    team2.add_player(IndividualPlayer("P3", "p3")) # Numer w rosterze: 1
    
    s.teams = [team1, team2]
    
    # Mock clock interaction
    s.clock = MagicMock()
    s.clock.total_minutes = 90
    s.clock.current_period_minutes = 45
    return s

@pytest.fixture
def mock_clock_limit(monkeypatch):
    monkeypatch.setattr('src.sports.football.console.football_command_parser.match_clock_limit', lambda s: 90)


def test_empty_command(state, capsys):
    assert parse_football_command("", state) is None
    assert "Empty command" in capsys.readouterr().out


def test_start_end(state):
    assert isinstance(parse_football_command("start", state), StartMatch)
    assert isinstance(parse_football_command("end", state), EndPeriod)


def test_roster(state, capsys, monkeypatch):
    monkeypatch.setattr('src.sports.football.console.football_command_parser.print_roster_report', MagicMock())
    
    # Valid
    assert parse_football_command("roster", state) is None
    assert parse_football_command("roster 1", state) is None
    
    # Invalid team
    assert parse_football_command("roster abc", state) is None
    assert "Team must be a number" in capsys.readouterr().out
    
    # Too many parts
    assert parse_football_command("roster 1 2", state) is None
    assert "Usage: roster" in capsys.readouterr().out


def test_goals(state, mock_clock_limit):
    # Valid goal: team 1, min 10, player 1 (maps to "p1")
    cmd = parse_football_command("goal 1 10 1", state)
    assert isinstance(cmd, ScoreGoal)
    assert cmd.team_index == 0
    assert cmd.minute == 10
    assert cmd.scorer_id == "p1"
    assert not cmd.own_goal
    assert not cmd.penalty

    # Own goal without scorer: team 2, min 45
    cmd = parse_football_command("og 2 45", state)
    assert isinstance(cmd, ScoreGoal)
    assert cmd.team_index == 1
    assert cmd.minute == 45
    assert cmd.scorer_id is None
    assert cmd.own_goal

    # Penalty: team 1, min 90, player 2 (maps to "p2")
    cmd = parse_football_command("pen 1 90 2", state)
    assert isinstance(cmd, ScoreGoal)
    assert cmd.penalty

    # Invalid
    assert parse_football_command("goal 3 10", state) is None
    assert parse_football_command("goal abc 10", state) is None
    assert parse_football_command("goal 1 abc", state) is None
    assert parse_football_command("goal 1 10 99", state) is None


def test_fouls(state, mock_clock_limit):
    # Valid foul: team 1, player 1 ("p1"), min 10
    cmd = parse_football_command("foul 1 1 10", state)
    assert isinstance(cmd, CommitFoul)
    assert cmd.team_index == 0
    assert cmd.offender_id == "p1"
    assert cmd.minute == 10
    assert cmd.card is None
    assert cmd.reason == "Foul play"

    # Yellow card with reason: team 2, player 1 ("p3"), min 20
    cmd = parse_football_command("yellow 2 1 20 bad tackle", state)
    assert isinstance(cmd, CommitFoul)
    assert cmd.card == "yellow"
    assert cmd.reason == "bad tackle"

    # Red card: team 1, player 2 ("p2"), min 90
    cmd = parse_football_command("red 1 2 90", state)
    assert isinstance(cmd, CommitFoul)
    assert cmd.card == "red"

    # Invalid
    assert parse_football_command("foul abc 1 10", state) is None
    assert parse_football_command("foul 1 99 10", state) is None
    assert parse_football_command("foul 1 1 abc", state) is None


def test_lineup(state):
    # lineup team 1, player 1 starting (p1)
    cmd = parse_football_command("lineup 1 1", state)
    assert isinstance(cmd, SubmitLineup)
    assert cmd.team_index == 0
    assert cmd.starting == ("p1",)
    assert cmd.bench == ("p2",)

    # Invalid
    assert parse_football_command("lineup abc 1", state) is None
    assert parse_football_command("lineup 1 99", state) is None


def test_sub(state, mock_clock_limit):
    # sub team 1, out 1 ("p1"), in 2 ("p2"), min 45
    cmd = parse_football_command("sub 1 1 2 45", state)
    assert isinstance(cmd, SubstitutePlayer)
    assert cmd.team_index == 0
    assert cmd.player_out == "p1"
    assert cmd.player_in == "p2"
    assert cmd.minute == 45

    # Without minute
    cmd = parse_football_command("sub 1 1 2", state)
    assert cmd.minute == 0

    # Invalid
    assert parse_football_command("sub abc 1 2", state) is None
    assert parse_football_command("sub 1 99 2", state) is None
    assert parse_football_command("sub 1 1 99", state) is None
    assert parse_football_command("sub 1 1 2 abc", state) is None


def test_pk(state, capsys):
    # Not in penalties phase
    assert parse_football_command("pk 1 g", state) is None
    assert "Penalty kicks are only available" in capsys.readouterr().out

    # In penalties phase
    state.phase = MatchPhase.PENALTIES
    cmd = parse_football_command("pk 1 g", state)
    assert isinstance(cmd, TakePenaltyKick)
    assert cmd.team_index == 0
    assert cmd.scored is True

    cmd = parse_football_command("pk 2 m", state)
    assert cmd.team_index == 1
    assert cmd.scored is False

    # Invalid team & outcome
    assert parse_football_command("pk abc g", state) is None
    assert parse_football_command("pk 1 x", state) is None
    assert "must be 'g' (goal) or 'm'" in capsys.readouterr().out


def test_invalid_syntax(state, capsys):
    assert parse_football_command("unknown_cmd", state) is None
    assert "Invalid syntax" in capsys.readouterr().out