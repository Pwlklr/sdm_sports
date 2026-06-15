from __future__ import annotations

from src.core.contestant.models import IndividualPlayer
from src.core.sport.match_setup import create_console_contest
from src.sports.darts.adapter import DartsConsoleAdapter
from src.sports.darts.contest.commands import RevokeDartThrow, StartMatch, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT


def _match():
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    adapter = DartsConsoleAdapter()
    match = create_console_contest(
        DARTS_SPORT.id, adapter, players, DartsMatchConfig()
    )
    match.handle(StartMatch())
    return match, adapter


def test_reverse_lists_dart_events(capsys) -> None:
    match, adapter = _match()
    match.handle(ThrowDart(sector=20, multiplier=1))

    assert adapter.parse_command("reverse", match) is None
    output = capsys.readouterr().out
    assert "1." in output
    assert "20" in output


def test_reverse_by_number_returns_command() -> None:
    match, adapter = _match()
    match.handle(ThrowDart(sector=20, multiplier=1))

    cmd = adapter.parse_command("reverse 1", match)
    assert isinstance(cmd, RevokeDartThrow)
