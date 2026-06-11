from unittest.mock import patch

from src.core.contestant.models import IndividualPlayer, Team
from src.core.sport.match_setup import create_console_contest
from src.sports.football.adapter import FootballConsoleAdapter
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    TakePenaltyKick,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.state import MatchPhase
from src.sports.football.descriptor import FOOTBALL_SPORT


def _adapter() -> FootballConsoleAdapter:
    return FootballConsoleAdapter()


def _match() -> object:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "player-striker-1"))
    away.add_player(IndividualPlayer("Defender", "player-defender-2"))
    match = create_console_contest(
        FOOTBALL_SPORT.id, _adapter(), [home, away], FootballMatchConfig()
    )
    match.handle(StartMatch())
    return match


def test_adapter_descriptor() -> None:
    assert _adapter().descriptor == FOOTBALL_SPORT


def test_adapter_get_start_command() -> None:
    assert isinstance(_adapter().get_start_command(), StartMatch)


def test_adapter_parse_via_parser_module() -> None:
    adapter = _adapter()
    match = _match()

    goal = adapter.parse_command("goal 1 23 1", match)
    assert isinstance(goal, ScoreGoal)
    assert goal.minute == 23

    foul = adapter.parse_command("foul 1 1 15 tactical foul", match)
    assert isinstance(foul, CommitFoul)
    assert foul.card is None
    assert foul.reason == "tactical foul"

    yellow = adapter.parse_command("yellow 1 1 30", match)
    assert isinstance(yellow, CommitFoul)

    assert isinstance(adapter.parse_command("end", match), EndPeriod)


def test_adapter_parse_penalty_command() -> None:
    adapter = _adapter()
    match = _match()
    match.current_state.phase = MatchPhase.PENALTIES  # type: ignore[attr-defined]

    cmd = adapter.parse_command("pk 1 g", match)
    assert isinstance(cmd, TakePenaltyKick)
    assert cmd.scored is True


@patch("builtins.input", side_effect=["2", "45", "y"])
def test_collect_config(mock_input: object) -> None:
    config = _adapter().collect_config()
    assert config.number_of_halves == 2
