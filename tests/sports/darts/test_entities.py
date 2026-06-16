from src.sports.darts.contestant.dart_player import DartPlayer
from src.sports.darts.contest.entities import DartThrow, DartTurn


def test_dart_throw_value_object() -> None:
    throw = DartThrow(sector=20, multiplier=3)
    assert throw.points == 60


def test_dart_turn_collects_throws() -> None:
    turn = DartTurn()
    turn = turn.with_throw(DartThrow(sector=20, multiplier=3))
    turn = turn.with_throw(DartThrow(sector=5, multiplier=1))
    assert turn.total_points == 65
    assert len(turn.throws) == 2


def test_dart_throw_stores_values_without_domain_validation() -> None:
    throw = DartThrow(sector=99, multiplier=1)
    assert throw.sector == 99
    assert throw.points == 99


def test_dart_player_str_and_id() -> None:
    player = DartPlayer(contestant_id="player_1", name="Luke Littler")
    assert str(player) == "Luke Littler"
    assert player.id == "player_1"
