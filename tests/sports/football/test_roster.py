from src.core.contestant.models import IndividualPlayer, Team

from src.sports.football.contest.football_match_config import FootballMatchConfig

from src.sports.football.contest.player_stats import FootballPlayerStats

from src.sports.football.console.roster_parser import parse_console_team_number
from src.sports.football.contest.roster import (
    player_on_team,
    resolve_roster_player_by_number,
)

from src.sports.football.contest.roster_status import team_disciplinary_summary

from src.sports.football.contest.football_contest_state import (
    create_football_contest_state,
)


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

    away = Team("Away", "away")

    state = create_football_contest_state([team, away], FootballMatchConfig())

    stats = dict(state.player_stats)

    stats["player-saka-001"] = FootballPlayerStats(
        player_id="player-saka-001", yellow_cards=1
    )

    stats["player-odegaard-2"] = FootballPlayerStats(
        player_id="player-odegaard-2", dismissed=True
    )

    from dataclasses import replace

    state = replace(state, player_stats=stats)

    yellows, sent_off = team_disciplinary_summary(team, state)

    assert yellows == 1

    assert sent_off == 1
