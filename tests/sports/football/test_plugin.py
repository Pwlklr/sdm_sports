from unittest.mock import patch

from src.core.contestant import Team
from src.sports.football.commands import (
    CommitFoulCommand,
    EndPeriodCommand,
    PenaltyKickCommand,
    ScoreGoalCommand,
    StartFootballMatchCommand,
)
from src.sports.football.config import FootballMatchConfig
from src.sports.football.plugin import FootballPlugin
from src.sports.football.state import MatchPhase


def _match() -> object:
    plugin = FootballPlugin()
    home = Team("Home", "home")
    away = Team("Away", "away")
    return plugin.create_tournament_match([home, away], FootballMatchConfig())


def test_plugin_name() -> None:
    assert FootballPlugin().name == "Association Football (Soccer)"


def test_plugin_get_start_command() -> None:
    cmd = FootballPlugin().get_start_command()
    assert isinstance(cmd, StartFootballMatchCommand)


def test_plugin_get_input_prompt() -> None:
    plugin = FootballPlugin()
    match = _match()
    prompt = plugin.get_input_prompt(match)
    assert "goal" in prompt
    assert "end" in prompt


@patch("builtins.input", side_effect=["2", "45", "y"])
def test_setup_tournament_config(mock_input: object) -> None:
    plugin = FootballPlugin()
    config = plugin.setup_tournament_config()
    assert isinstance(config, FootballMatchConfig)
    assert config.number_of_halves == 2
    assert config.allow_draw is True


def test_create_tournament_match() -> None:
    plugin = FootballPlugin()
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(half_length_minutes=30)
    match = plugin.create_tournament_match([home, away], config)
    assert match is not None


def test_parse_valid_commands() -> None:
    plugin = FootballPlugin()
    match = _match()

    assert isinstance(plugin.parse_command("goal 0", match), ScoreGoalCommand)
    assert isinstance(plugin.parse_command("og 1", match), ScoreGoalCommand)
    assert isinstance(plugin.parse_command("yellow 0 p9", match), CommitFoulCommand)
    assert isinstance(plugin.parse_command("red 1", match), CommitFoulCommand)
    assert isinstance(plugin.parse_command("foul 0", match), CommitFoulCommand)
    assert isinstance(plugin.parse_command("end", match), EndPeriodCommand)


def test_parse_penalty_command() -> None:
    plugin = FootballPlugin()
    match = _match()
    match.current_state.phase = MatchPhase.PENALTIES  # type: ignore[attr-defined]

    cmd = plugin.parse_command("pk 0 g", match)
    assert isinstance(cmd, PenaltyKickCommand)
    assert cmd.scored is True

    prompt = plugin.get_input_prompt(match)
    assert "Penalty" in prompt


def test_parse_invalid_commands() -> None:
    plugin = FootballPlugin()
    match = _match()

    assert plugin.parse_command("", match) is None
    assert plugin.parse_command("goal 5", match) is None
    assert plugin.parse_command("goal x", match) is None
    assert plugin.parse_command("nonsense", match) is None
    assert plugin.parse_command("pk 0 x", match) is None
