import pytest
from src.core.contestant import IndividualPlayer
from src.core.tournament_phase import TournamentPhase
from src.core.draw_strategies import RandomDrawStrategy

class DummyPhase(TournamentPhase):
    """Concrete implementation of the abstract TournamentPhase for testing."""
    pass

def test_random_knockout_draw_strategy() -> None:
    strategy = RandomDrawStrategy()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    p3 = IndividualPlayer("P3")
    p4 = IndividualPlayer("P4")
    
    contestants = [p1, p2, p3, p4]
    matchups = strategy.generate_draw(contestants)
    
    # 4 players should result in exactly 2 matches
    assert len(matchups) == 2
    
    # Each match must have exactly 2 players
    assert len(matchups[0]) == 2
    assert len(matchups[1]) == 2
    
    # Verify every player is scheduled exactly once
    drawn_players = [player for match in matchups for player in match]
    assert set(drawn_players) == set(contestants)
    assert len(drawn_players) == 4

def test_knockout_draw_handles_odd_numbers() -> None:
    strategy = RandomDrawStrategy()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    p3 = IndividualPlayer("P3")
    
    matchups = strategy.generate_draw([p1, p2, p3])
    # 3 players should result in 1 match (the remaining player gets a bye/is skipped)
    assert len(matchups) == 1

def test_tournament_phase_delegation() -> None:
    strategy = RandomDrawStrategy()
    phase = DummyPhase("Quarter Finals", strategy)
    
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    
    matchups = phase.get_matchups([p1, p2])
    
    assert phase.name == "Quarter Finals"
    assert len(matchups) == 1
    assert not phase.is_completed