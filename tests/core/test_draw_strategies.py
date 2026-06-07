import pytest
from src.core.contestant import Contestant
from src.core.draw_strategies import RandomDrawStrategy, RoundRobinDrawStrategy

class DummyContestant(Contestant):
    def __init__(self, name: str, contestant_id: str) -> None:
        self._name = name
        self._id = contestant_id

    @property
    def name(self) -> str: return self._name
    @property
    def id(self) -> str: return self._id
    @property
    def display_name(self) -> str: return self._name

@pytest.fixture
def roster() -> list[Contestant]:
    return [
        DummyContestant("A", "1"),
        DummyContestant("B", "2"),
        DummyContestant("C", "3"),
        DummyContestant("D", "4")
    ]

def test_random_draw_strategy_even(roster: list[Contestant]) -> None:
    strategy = RandomDrawStrategy()
    matchups = strategy.generate_draw(roster)
    
    # 4 players = 2 matches
    assert len(matchups) == 2
    
    # Ensure no player plays themselves
    for m in matchups:
        assert m[0] != m[1]

def test_random_draw_strategy_odd(roster: list[Contestant]) -> None:
    roster.append(DummyContestant("E", "5"))
    strategy = RandomDrawStrategy()
    matchups = strategy.generate_draw(roster)
    
    # 5 players = 2 matches (1 player sits out)
    assert len(matchups) == 2

def test_round_robin_draw_strategy(roster: list[Contestant]) -> None:
    strategy = RoundRobinDrawStrategy()
    matchups = strategy.generate_draw(roster)
    
    # Formula for Round Robin matches: N(N-1)/2. For 4 players = 6 matches.
    assert len(matchups) == 6
    
    # Verify A plays exactly 3 matches
    matches_with_A = [m for m in matchups if m[0].name == "A" or m[1].name == "A"]
    assert len(matches_with_A) == 3