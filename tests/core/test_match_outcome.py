from src.core.tournament.match_outcome import HeadToHeadPoints
from src.core.contestant.models import Contestant

class DummyContestant(Contestant):
    """A minimal concrete implementation for testing purposes."""
    def __init__(self, contestant_id: str, name: str = "Dummy"):
        self._contestant_id = contestant_id
        self._name = name

    @property
    def contestant_id(self) -> str:
        return self._contestant_id

    @property
    def display_name(self) -> str:
        return self._name

def test_head_to_head_points_initialization() -> None:
    """Verifies that the dataclass correctly holds match outcome data."""
    side_a = DummyContestant("team_A", "Team A")
    side_b = DummyContestant("team_B", "Team B")
    
    outcome = HeadToHeadPoints(side_a=side_a, side_b=side_b, points_a=3, points_b=1)
    
    assert outcome.side_a.contestant_id == "team_A"
    assert outcome.side_b.contestant_id == "team_B"
    assert outcome.points_a == 3
    assert outcome.points_b == 1