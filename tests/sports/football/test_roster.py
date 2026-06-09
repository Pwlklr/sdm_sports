import pytest

from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.roster import (
    parse_console_player_number,
    parse_console_team_number,
    player_on_team,
    resolve_roster_player_by_number,
)
from src.sports.football.contest.roster_status import team_disciplinary_summary
from src.sports.football.contest.entities import DisciplinaryRecord


def _team() -> Team:
    team = Team("Home", "home")
    team.add_player(IndividualPlayer("Saka", "player-saka-001"))
    team.add_player(IndividualPlayer("Odegaard", "player-odegaard-2"))
    return team


def test_parse_console_team_number() -> None:
    assert parse_console_team_number("1", 2) == 0
    assert parse_console_team_number("2", 2) == 1
    assert parse_console_team_number("3", 2) is None


def test_resolve_roster_player_by_number() -> None:
    team = _team()
    player = resolve_roster_player_by_number(team, 1)
    assert player.name == "Saka"


def test_player_on_team() -> None:
    team = _team()
    assert player_on_team(team, "player-saka-001")
    assert not player_on_team(team, "unknown")


def test_team_disciplinary_summary_counts_players() -> None:
    team = _team()
    record = DisciplinaryRecord()
    record.record_yellow("player-saka-001")
    record.dismiss("player-odegaard-2")

    yellows, sent_off = team_disciplinary_summary(team, record)
    assert yellows == 1
    assert sent_off == 1
