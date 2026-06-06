import pytest
import sys
from unittest.mock import patch, MagicMock
from src.console.main import TournamentEngine, SDMSportsApp
from src.sports.darts.plugin import DartsPlugin
from src.core.contestant import Contestant

def test_app_invalid_choice():
    app = SDMSportsApp()
    # Simulate user typing '99' for the discipline choice
    with patch('builtins.input', side_effect=['99']):
        with pytest.raises(SystemExit):
            app.run()

def test_app_run_quit_mid_match():
    app = SDMSportsApp()
    # Simulate: Pick Darts(1), 2 players, Names P1/P2, Enter to start (''), 'q' to quit
    with patch('builtins.input', side_effect=['1', '2', 'P1', 'P2', '', 'q']):
        with pytest.raises(SystemExit):
            app.run()

def test_tournament_odd_players_bye():
    engine = TournamentEngine(DartsPlugin())
    # 3 players means 1 gets a bye round
    with patch('builtins.input', side_effect=['3', 'A', 'B', 'C', '', 'q']):
        with pytest.raises(SystemExit):
            engine.run()

def test_play_match_winner_advances():
    engine = TournamentEngine(DartsPlugin())
    
    p1 = MagicMock(spec=Contestant)
    p1.contestant_id = "p1"
    p1.name = "A"
    p2 = MagicMock(spec=Contestant)
    p2.contestant_id = "p2"
    p2.name = "B"
    
    # Force the match to be instantly "completed" so we don't need to play it
    mock_contest = MagicMock()
    mock_contest.current_state.is_completed = True
    mock_contest.current_state.winner_id = "p1"
    
    engine.plugin.create_match = MagicMock(return_value=mock_contest)
    engine.plugin.parse_command = MagicMock(return_value=None)
    
    # Press enter ('') to start. It instantly ends and returns p1.
    with patch('builtins.input', side_effect=['', 'some_command']):
        winner = engine.play_match(p1, p2)
        assert winner == p1
        
def test_play_match_execute_command():
    engine = TournamentEngine(DartsPlugin())
    p1 = MagicMock(spec=Contestant); p1.name = "A"
    p2 = MagicMock(spec=Contestant); p2.name = "B"
    
    mock_contest = MagicMock()
    mock_contest.current_state.is_completed = False
    
    mock_command = MagicMock()
    engine.plugin.create_match = MagicMock(return_value=mock_contest)
    engine.plugin.parse_command = MagicMock(return_value=mock_command)
    
    # Press enter (''), execute a valid command ('throw'), then quit ('q')
    with patch('builtins.input', side_effect=['', 'throw', 'q']):
        with pytest.raises(SystemExit):
            engine.play_match(p1, p2)
            
    mock_command.execute.assert_called_once()