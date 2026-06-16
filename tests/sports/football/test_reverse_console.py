from __future__ import annotations

from src.core.contestant.models import IndividualPlayer, Team
from src.console.match_setup import create_console_contest
from src.sports.football.adapter import FootballConsoleAdapter
from src.sports.football.contest.commands import (
    RevokeCaution,
    ScoreGoal,
    StartMatch,
    VarOverturnGoal,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT
from tests.sports.football.lineup_helpers import submit_all_lineups


def _match():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    adapter = FootballConsoleAdapter()
    config = FootballMatchConfig(players_on_pitch=1, min_players_on_pitch=1)
    match = create_console_contest(
        FOOTBALL_SPORT.id, adapter, [home, away], config
    )
    match.handle(StartMatch())
    submit_all_lineups(match)
    return match, adapter


def test_reverse_lists_numbered_events(capsys) -> None:
    match, adapter = _match()
    match.handle(ScoreGoal(team_index=0, minute=10))
    match.handle(ScoreGoal(team_index=0, minute=20))

    assert adapter.parse_command("reverse", match) is None
    output = capsys.readouterr().out
    assert "1." in output
    assert "2." in output
    assert "10'" in output
    assert "20'" in output


def test_reverse_by_number_returns_var_for_goal() -> None:
    match, adapter = _match()
    match.handle(ScoreGoal(team_index=0, minute=10))

    cmd = adapter.parse_command("reverse 1", match)
    assert isinstance(cmd, VarOverturnGoal)
    assert cmd.reason == "reverse"


def test_var_by_number_only_lists_goals(capsys) -> None:
    match, adapter = _match()
    match.handle(ScoreGoal(team_index=0, minute=10))

    adapter.parse_command("var", match)
    output = capsys.readouterr().out
    assert "1." in output
    assert "gol" in output.lower() or "10'" in output


def test_revoke_caution_command_from_reverse() -> None:
    from src.sports.football.contest.commands import CommitFoul

    match, adapter = _match()
    match.handle(CommitFoul(team_index=0, minute=5, card="yellow", offender_id="p9"))

    cmd = adapter.parse_command("reverse 1", match)
    assert isinstance(cmd, RevokeCaution)
