import pytest
from src.sports.darts.entities import DartThrow, DartTurn

def test_valid_dart_throws() -> None:
    t1 = DartThrow(sector=20, multiplier=3)
    assert t1.points == 60
    assert str(t1) == "Treble 20"

    t2 = DartThrow(sector=25, multiplier=2)
    assert t2.points == 50
    assert str(t2) == "Double 25"

def test_miss_dart_throw() -> None:
    # A miss (0) is a perfectly valid throw in the domain
    t1 = DartThrow(sector=0, multiplier=1)
    assert t1.points == 0
    assert str(t1) == "Miss (0)"
    
    # Even if UI accidentally sends a multiplier with a miss, it normalizes
    t2 = DartThrow(sector=0, multiplier=3)
    assert t2.points == 0
    assert t2.multiplier == 1

def test_invalid_dart_throws() -> None:
    # Invalid sectors
    with pytest.raises(ValueError):
        DartThrow(sector=21, multiplier=1)
    with pytest.raises(ValueError):
        DartThrow(sector=-1, multiplier=1)
        
    # Invalid multipliers
    with pytest.raises(ValueError):
        DartThrow(sector=20, multiplier=4)
        
    # Invalid bullseye combinations
    with pytest.raises(ValueError):
        DartThrow(sector=25, multiplier=3)

def test_dart_turn_lifecycle() -> None:
    turn = DartTurn()
    assert not turn.is_finished
    assert turn.total_points == 0
    
    # Throw 1
    turn.add_throw(DartThrow(20, 3))
    assert not turn.is_finished
    assert turn.total_points == 60
    assert len(turn.throws) == 1
    
    # Throw 2
    turn.add_throw(DartThrow(20, 1))
    assert not turn.is_finished
    assert turn.total_points == 80
    
    # Throw 3
    turn.add_throw(DartThrow(0, 1)) # Miss!
    assert turn.is_finished
    assert turn.total_points == 80
    
    # Try throwing a 4th dart
    with pytest.raises(ValueError):
        turn.add_throw(DartThrow(1, 1))

def test_busted_dart_turn() -> None:
    turn = DartTurn()
    turn.add_throw(DartThrow(20, 3))
    
    assert not turn.is_finished
    
    # External disciplinary engine flags it as busted
    turn.mark_busted()
    
    assert turn.is_busted
    assert turn.is_finished
    
    # Cannot throw after bust
    with pytest.raises(ValueError):
        turn.add_throw(DartThrow(1, 1))