from unittest.mock import patch

from src.core.contestant.models import IndividualPlayer
from src.core.sport.match_setup import create_console_contest
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.contest.commands import CallOcheFault, StartMatch, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.darts_sport_factory import DartsSportFactory
from src.sports.darts.descriptor import DARTS_SPORT


def _adapter() -> DartsConsoleAdapter:
    return DartsConsoleAdapter()


def _factory() -> DartsSportFactory:
    return DartsSportFactory()


def _match(*players: IndividualPlayer):
    factory = _factory()
    adapter = _adapter()
    contestants = list(players) if players else [IndividualPlayer("P1")]
    return create_console_contest(
        factory, adapter, contestants, DartsMatchConfig()
    )


def test_adapter_descriptor() -> None:
    assert _adapter().descriptor == DARTS_SPORT


def test_adapter_get_start_command() -> None:
    cmd = _adapter().get_start_command()
    assert isinstance(cmd, StartMatch)


def test_adapter_get_input_prompt() -> None:
    p1 = IndividualPlayer("P1")
    match = _match(p1, p1)
    prompt = _adapter().get_input_prompt(match)
    assert "Action" in prompt


@patch("builtins.input", side_effect=["501", "1", "1", "1", "2"])
def test_collect_config(mock_input: object) -> None:
    config = _adapter().collect_config()
    assert isinstance(config, DartsMatchConfig)
    assert config.starting_score == 501


def test_create_console_contest() -> None:
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    config = DartsMatchConfig(starting_score=301)
    match = create_console_contest(_factory(), _adapter(), [p1, p2], config)
    assert match.current_state.starting_score == 301


def test_adapter_parse_valid_command() -> None:
    adapter = _adapter()
    match = _match(IndividualPlayer("P1"))

    cmd = adapter.parse_command("20 3", match)
    assert isinstance(cmd, ThrowDart)
    assert cmd.sector == 20
    assert cmd.multiplier == 3

    cmd_fault = adapter.parse_command("fault", match)
    assert isinstance(cmd_fault, CallOcheFault)


def test_adapter_parse_invalid_commands() -> None:
    adapter = _adapter()
    match = _match(IndividualPlayer("P1"))

    assert adapter.parse_command("invalid string", match) is None
    assert adapter.parse_command("99 1", match) is None
