import pytest
from src.sports.darts.plugin import DartsPlugin
from src.sports.darts.player import DartPlayer
from src.core.contest import Contest
from src.sports.darts.commands import ThrowDartCommand

def test_plugin_create_match():
    plugin = DartsPlugin()
    players = [DartPlayer("p1", "A"), DartPlayer("p2", "B")]
    match = plugin.create_match(players)
    
    assert isinstance(match, Contest)
    assert len(match.current_state.players) == 2

def test_plugin_parse_valid_command():
    plugin = DartsPlugin()
    match = plugin.create_match([DartPlayer("p1", "A"), DartPlayer("p2", "B")])
    
    cmd = plugin.parse_command("20 3", match)
    assert isinstance(cmd, ThrowDartCommand)
    assert cmd.sector == 20
    assert cmd.multiplier == 3

def test_plugin_parse_invalid_commands():
    plugin = DartsPlugin()
    match = plugin.create_match([DartPlayer("p1", "A"), DartPlayer("p2", "B")])
    
    assert plugin.parse_command("100 1", match) is None  # Invalid sector
    assert plugin.parse_command("20 5", match) is None   # Invalid multiplier
    assert plugin.parse_command("50 3", match) is None   # Invalid treble bull
    assert plugin.parse_command("invalid string", match) is None

def test_plugin_interactive_setup_fallback():
    from src.sports.darts.plugin import DartsPlugin
    plugin = DartsPlugin()
    match = plugin.interactive_setup()
    assert match is not None
    assert len(match.current_state.players) == 2