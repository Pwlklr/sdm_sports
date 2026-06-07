import pytest
from unittest.mock import MagicMock
from src.core.contest import Contest
from src.sports.darts.state import DartsContestState
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.player import DartPlayer
from src.console.darts_view import DartsConsoleView

def test_darts_scoreboard_prints_correctly(capsys: pytest.CaptureFixture[str]) -> None:
    players = [DartPlayer("p1", "Littler"), DartPlayer("p2", "Humphries")]
    config = DartsMatchConfig(starting_score=501)
    state = DartsContestState(players=players, config=config)
    
    mock_contest = MagicMock(spec=Contest)
    mock_contest.current_state = state
    
    observer = DartsConsoleView()
    observer.update(mock_contest)
    
    captured = capsys.readouterr()
    assert "DARTS SCOREBOARD" in captured.out
    assert ">> Littler" in captured.out 
    assert "501" in captured.out