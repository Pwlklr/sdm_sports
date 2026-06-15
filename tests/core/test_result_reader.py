from unittest.mock import MagicMock
from src.core.tournament.result_reader import NullTournamentResultReader

def test_null_tournament_result_reader() -> None:
    """Verifies the Null Object pattern implementation returns safe defaults."""
    reader = NullTournamentResultReader()
    contest = MagicMock()
    result = MagicMock()
    
    assert reader.read_head_to_head(contest, result) is None
    assert reader.read_knockout_winner(contest, result) is None
    assert reader.describe_result(contest, result) == "zakonczony"