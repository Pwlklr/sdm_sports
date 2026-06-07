import pytest
from unittest.mock import patch
from src.sports.darts.plugin import DartsPlugin
from src.core.contestant import IndividualPlayer
from src.sports.darts.commands import ThrowDartCommand, OcheFaultCommand, StartDartsMatchCommand
from src.sports.darts.config import DartsMatchConfig

def test_plugin_name() -> None:
    assert DartsPlugin().name == "Professional Darts (X01)"

def test_plugin_get_start_command() -> None:
    cmd = DartsPlugin().get_start_command()
    assert isinstance(cmd, StartDartsMatchCommand)

def test_plugin_get_input_prompt() -> None:
    plugin = DartsPlugin()
    p1 = IndividualPlayer("P1")
    match = plugin.create_tournament_match([p1], DartsMatchConfig())
    prompt = plugin.get_input_prompt(match)
    assert "Action" in prompt
    assert "sector" in prompt

# Added two '1's to the end of the side effect to satisfy In/Out multipliers
@patch('builtins.input', side_effect=['501', '1', '1', '1', '2'])
def test_setup_tournament_config(mock_input: object) -> None:
    plugin = DartsPlugin()
    config = plugin.setup_tournament_config()
    assert isinstance(config, DartsMatchConfig)
    assert config.starting_score == 501
    assert config.in_multiplier == 1
    assert config.out_multiplier == 2

def test_create_tournament_match() -> None:
    plugin = DartsPlugin()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    config = DartsMatchConfig(starting_score=301)
    
    match = plugin.create_tournament_match([p1, p2], config)
    assert match is not None
    assert match.current_state.starting_score == 301

def test_plugin_parse_valid_command() -> None:
    plugin = DartsPlugin()
    p1 = IndividualPlayer("P1")
    match = plugin.create_tournament_match([p1], DartsMatchConfig())
    
    cmd = plugin.parse_command("20 3", match)
    assert isinstance(cmd, ThrowDartCommand)
    assert cmd.sector == 20
    assert cmd.multiplier == 3

    cmd_miss = plugin.parse_command("0", match)
    assert isinstance(cmd_miss, ThrowDartCommand)
    assert cmd_miss.sector == 0

    cmd_fault = plugin.parse_command("fault", match)
    assert isinstance(cmd_fault, OcheFaultCommand)

def test_plugin_parse_invalid_commands() -> None:
    plugin = DartsPlugin()
    p1 = IndividualPlayer("P1")
    match = plugin.create_tournament_match([p1], DartsMatchConfig())
    
    assert plugin.parse_command("invalid string", match) is None
    assert plugin.parse_command("99 1", match) is None
    assert plugin.parse_command("20 4", match) is None
    assert plugin.parse_command("25 3", match) is None