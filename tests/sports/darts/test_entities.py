from src.sports.darts.contest.entities import DartThrow, DartTurn

def test_dart_throw_value_object() -> None:
    throw = DartThrow(20, 3)
    assert throw.points == 60


def test_dart_turn_collects_throws() -> None:
    turn = DartTurn()
    turn.add_throw(DartThrow(20, 3))
    turn.add_throw(DartThrow(5, 1))
    assert turn.total_points == 65
    assert len(turn.throws) == 2


def test_dart_throw_stores_values_without_domain_validation() -> None:
    throw = DartThrow(99, 1)
    assert throw.sector == 99
    assert throw.points == 99
