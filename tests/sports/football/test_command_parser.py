import pytest

from dataclasses import replace

from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.console.football_command_parser import parse_football_command
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    TakePenaltyKick,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.state import FootballContestState, MatchPhase, create_football_contest_state
from src.sports.football.contest.events import MatchStarted, PeriodStarted
from src.sports.football.contest.entities import PeriodKind


def _state() -> FootballContestState:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "striker"))
    away.add_player(IndividualPlayer("Defender", "defender"))
    state = create_football_contest_state([home, away], config=FootballMatchConfig())
    state = state.apply(MatchStarted())
    state = state.apply(PeriodStarted(kind=PeriodKind.REGULAR, index=0))
    return state


def test_parse_start_and_end() -> None:
    state = _state()
    assert isinstance(parse_football_command("start", state), StartMatch)
    assert isinstance(parse_football_command("end", state), EndPeriod)


def test_parse_goal_with_all_fields() -> None:
    state = _state()
    cmd = parse_football_command("pen 1 40 1", state)
    assert isinstance(cmd, ScoreGoal)
    assert cmd.team_index == 0
    assert cmd.minute == 40
    assert cmd.scorer_id == "striker"
    assert cmd.penalty is True
    assert cmd.own_goal is False


def test_parse_yellow_with_reason() -> None:
    state = _state()
    cmd = parse_football_command("yellow 2 1 30 reckless challenge", state)
    assert isinstance(cmd, CommitFoul)
    assert cmd.team_index == 1
    assert cmd.offender_id == "defender"
    assert cmd.minute == 30
    assert cmd.card == "yellow"
    assert cmd.reason == "reckless challenge"


def test_parse_foul_without_card() -> None:
    state = _state()
    cmd = parse_football_command("foul 1 1 15 holding", state)
    assert isinstance(cmd, CommitFoul)
    assert cmd.card is None
    assert cmd.reason == "holding"


def test_parse_roster_query(capsys: pytest.CaptureFixture[str]) -> None:
    from src.sports.football.contest.roster_status import print_roster_report

    state = _state()
    print_roster_report(state, team_number=1)
    captured = capsys.readouterr()
    assert "Team 1: Home" in captured.out
    assert "Striker" in captured.out


def test_parse_roster_command(capsys: pytest.CaptureFixture[str]) -> None:
    state = _state()
    assert parse_football_command("roster 1", state) is None
    captured = capsys.readouterr()
    assert "Striker" in captured.out


def test_parse_penalty_kick() -> None:
    state = replace(_state(), phase=MatchPhase.PENALTIES)
    cmd = parse_football_command("pk 2 m", state)
    assert isinstance(cmd, TakePenaltyKick)
    assert cmd.team_index == 1
    assert cmd.scored is False
