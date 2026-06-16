from src.core.contest.contest_result import RankedEntry
from src.core.contestant.models import IndividualPlayer
from src.core.tournament.ranking import head_to_head_points


def test_head_to_head_points_from_ranking() -> None:
    side_a = IndividualPlayer("Team A", "team_a")
    side_b = IndividualPlayer("Team B", "team_b")
    ranking = (
        RankedEntry(contestant=side_a, place=1),
        RankedEntry(contestant=side_b, place=2),
    )

    points_a, points_b = head_to_head_points(side_a, side_b, ranking)

    assert points_a == 3
    assert points_b == 0


def test_head_to_head_points_draw() -> None:
    side_a = IndividualPlayer("Team A", "team_a")
    side_b = IndividualPlayer("Team B", "team_b")
    ranking = (
        RankedEntry(contestant=side_a, place=1),
        RankedEntry(contestant=side_b, place=1),
    )

    points_a, points_b = head_to_head_points(side_a, side_b, ranking)

    assert points_a == 1
    assert points_b == 1
