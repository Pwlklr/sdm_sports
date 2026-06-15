from unittest.mock import MagicMock, patch
from src.sports.football.tournament_result_reader import FootballTournamentResultReader

def test_football_tournament_result_reader_valid() -> None:
    reader = FootballTournamentResultReader()
    contest = MagicMock()
    side_a = MagicMock()
    side_b = MagicMock()
    contest.contestants = [side_a, side_b]
    
    result = MagicMock()
    result.ranking.return_value = (MagicMock(), MagicMock()) 
    
    with patch('src.sports.football.tournament_result_reader.head_to_head_points', return_value=(3, 0)):
        h2h = reader.read_head_to_head(contest, result)
        assert h2h is not None
        assert h2h.side_a == side_a
        assert h2h.side_b == side_b
        assert h2h.points_a == 3
        assert h2h.points_b == 0
        
    with patch('src.sports.football.tournament_result_reader.single_first_place', return_value=side_a):
        assert reader.read_knockout_winner(contest, result) == side_a
        
    with patch('src.sports.football.tournament_result_reader.describe_two_way_result', return_value="3 - 0"):
        assert reader.describe_result(contest, result) == "3 - 0"

def test_football_tournament_result_reader_edge_cases() -> None:
    reader = FootballTournamentResultReader()
    contest = MagicMock()
    result = MagicMock()
    
    # Edge Case 1: Not exactly 2 sides in the contest
    contest.contestants = [MagicMock()]
    assert reader.read_head_to_head(contest, result) is None
    
    # Edge Case 2: 2 sides, but the ranking is empty
    contest.contestants = [MagicMock(), MagicMock()]
    result.ranking.return_value = tuple()
    assert reader.read_head_to_head(contest, result) is None