import pytest
from dataclasses import replace
from unittest.mock import MagicMock

from src.core.contest import Contest
from src.core.contestant.models import IndividualPlayer
from src.sports.darts.contest.darts_contest_state import create_darts_contest_state
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.entities import DartThrow, DartTurn
from src.sports.darts.console.darts_console_view import DartsConsoleView


def test_darts_scoreboard_prints_correctly(capsys: pytest.CaptureFixture[str]) -> None:
    players = [IndividualPlayer("Littler"), IndividualPlayer("Humphries")]
    config = DartsMatchConfig(starting_score=501)
    state = replace(create_darts_contest_state(players, config), current_turn=DartTurn())

    mock_contest = MagicMock(spec=Contest)
    mock_contest.current_state = state

    DartsConsoleView().update(mock_contest, None)

    captured = capsys.readouterr()
    assert "DARTS SCOREBOARD" in captured.out
    assert ">> Littler" in captured.out
    assert "501" in captured.out
    assert "Dart 1 of 3" in captured.out


def test_scoreboard_after_last_dart_does_not_show_fourth_dart(
    capsys: pytest.CaptureFixture[str],
) -> None:
    players = [IndividualPlayer("Littler"), IndividualPlayer("Humphries")]
    turn = DartTurn()
    for sector, multiplier in [(20, 1), (20, 1), (20, 2)]:
        turn = turn.with_throw(DartThrow(sector=sector, multiplier=multiplier))
    state = replace(
        create_darts_contest_state(players, DartsMatchConfig()),
        current_turn=turn,
    )

    mock_contest = MagicMock(spec=Contest)
    mock_contest.current_state = state

    DartsConsoleView().update(mock_contest, None)

    captured = capsys.readouterr()
    assert "Dart 4 of 3" not in captured.out
    assert "Turn:" not in captured.out
