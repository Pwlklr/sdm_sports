import pytest
from unittest.mock import MagicMock, patch
from src.console.tournament_view import (
    active_matches,
    standings_table,
    _format_final_status,
    schedule_view,
)
from src.core.tournament.phase import GroupStagePhase
from src.core.contest import Contest
from src.core.contestant import IndividualPlayer


def test_active_matches():
    phase = MagicMock()
    c1 = MagicMock(spec=Contest)
    c1.current_state = MagicMock()
    c1.current_state.is_finished = False
    c2 = MagicMock(spec=Contest)
    c2.current_state = MagicMock()
    c2.current_state.is_finished = True
    phase.contests = [c1, c2]

    active = active_matches(phase)
    assert len(active) == 1
    assert active[0] == c1


def test_standings_table_not_group_stage():
    phase = MagicMock()
    res = standings_table(phase)
    assert "(brak tabeli dla tej fazy)" in res[0]


def test_standings_table_empty():
    phase = MagicMock(spec=GroupStagePhase)
    phase.standings = {}
    res = standings_table(phase)
    assert "(brak tabeli dla tej fazy)" in res[0]


def test_standings_table_with_data():
    phase = MagicMock(spec=GroupStagePhase)
    row1 = MagicMock()
    row1.points = 3
    row1.wins = 1
    row1.draws = 0
    row1.losses = 0
    row1.played = 1
    row1.contestant.name = "Team A"

    row2 = MagicMock()
    row2.points = 0
    row2.wins = 0
    row2.draws = 0
    row2.losses = 1
    row2.played = 1
    row2.contestant.name = "Team B"

    phase.standings = {"A": row1, "B": row2}

    lines = standings_table(phase)
    assert len(lines) == 3
    assert "Team A" in lines[1]
    assert "Team B" in lines[2]


@patch("src.console.tournament_view.describe_two_way_result")
def test_format_final_status(mock_describe):
    c = MagicMock(spec=Contest)
    c.current_state = MagicMock()

    # Not finished
    c.current_state.is_finished = False
    assert _format_final_status(c) == "oczekuje"

    # Finished, ValueError
    c.current_state.is_finished = True
    c.get_final_result.side_effect = ValueError
    assert _format_final_status(c) == "oczekuje"

    # Finished, valid result
    c.get_final_result.side_effect = None
    result_mock = MagicMock()
    c.get_final_result.return_value = result_mock
    mock_describe.return_value = "Wygral Team A"

    assert _format_final_status(c) == "Wygral Team A"
    mock_describe.assert_called_once_with(result_mock.ranking())


def test_schedule_view():
    phase = MagicMock()

    c1 = MagicMock(spec=Contest)
    c1.current_state = MagicMock()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    c1.contestants = [p1, p2]
    c1.current_state.is_finished = False

    c2 = MagicMock(spec=Contest)
    c2.current_state = MagicMock()
    p3 = IndividualPlayer("P3")
    c2.contestants = [p3]
    c2.current_state.is_finished = False

    phase.contests = [c1, c2]

    with patch(
        "src.console.tournament_view._format_final_status", return_value="status"
    ):
        lines = schedule_view(phase)
        assert len(lines) == 2
        assert "P1 (dom) vs P2 (wyjazd)" in lines[0]
        assert "P3" in lines[1]
        assert "status" in lines[0]
