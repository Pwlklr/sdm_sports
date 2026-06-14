from src.core.contest.contest_result import RankedEntry
from src.core.contestant.models import IndividualPlayer
from src.core.tournament.ranking import (
    describe_two_way_result,
    head_to_head_points,
    is_ex_aequo_first,
    qualifiers_up_to_place,
    single_first_place,
)


def _player(name: str, pid: str) -> IndividualPlayer:
    return IndividualPlayer(name, contestant_id=pid)


def test_single_first_place_ex_aequo_returns_none() -> None:
    a, b = _player("A", "a"), _player("B", "b")
    ranking = (RankedEntry(contestant=a, place=1), RankedEntry(contestant=b, place=1))
    assert single_first_place(ranking) is None
    assert is_ex_aequo_first(ranking)


def test_head_to_head_points_from_ranking() -> None:
    a, b = _player("A", "a"), _player("B", "b")
    ranking = (RankedEntry(contestant=a, place=1), RankedEntry(contestant=b, place=2))
    assert head_to_head_points(a, b, ranking) == (3, 0)

    draw = (RankedEntry(contestant=a, place=1), RankedEntry(contestant=b, place=1))
    assert head_to_head_points(a, b, draw) == (1, 1)


def test_qualifiers_up_to_place() -> None:
    players = [_player("A", "a"), _player("B", "b"), _player("C", "c")]
    ranking = (
        RankedEntry(contestant=players[0], place=1),
        RankedEntry(contestant=players[1], place=2),
        RankedEntry(contestant=players[2], place=3),
    )
    assert qualifiers_up_to_place(ranking, 2) == [players[0], players[1]]


def test_describe_two_way_result() -> None:
    a, b = _player("A", "a"), _player("B", "b")
    assert describe_two_way_result(()) == "zakonczony"
    assert describe_two_way_result((RankedEntry(contestant=a, place=1),)) == "wygral A"
    assert (
        describe_two_way_result(
            (RankedEntry(contestant=a, place=1), RankedEntry(contestant=b, place=1))
        )
        == "remis"
    )
