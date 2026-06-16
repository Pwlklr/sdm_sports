from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.core.contest.contest_result import RankedEntry
from src.core.contestant.models import Contestant


def single_first_place(ranking: tuple[RankedEntry, ...]) -> Contestant | None:
    """Return the sole contestant at place 1, or None if absent or ex-aequo."""
    first_place = [entry.contestant for entry in ranking if entry.place == 1]
    if len(first_place) == 1:
        return first_place[0]
    return None


def is_ex_aequo_first(ranking: tuple[RankedEntry, ...]) -> bool:
    """True when two or more contestants share first place."""
    return len([entry for entry in ranking if entry.place == 1]) > 1


def place_for(ranking: tuple[RankedEntry, ...], contestant_id: str) -> int | None:
    for entry in ranking:
        if entry.contestant.id == contestant_id:
            return entry.place
    return None


def head_to_head_points(
    side_a: Contestant,
    side_b: Contestant,
    ranking: tuple[RankedEntry, ...],
    *,
    win_points: int = 3,
    draw_points: int = 1,
) -> tuple[int, int]:
    """Standard 3-1-0 (or custom) points from ranking places for a two-way contest."""
    place_a = place_for(ranking, side_a.id)
    place_b = place_for(ranking, side_b.id)
    if place_a is None or place_b is None:
        return 0, 0
    if place_a == place_b:
        return draw_points, draw_points
    if place_a < place_b:
        return win_points, 0
    return 0, win_points


def qualifiers_up_to_place(
    ranking: tuple[RankedEntry, ...], max_place: int
) -> list[Contestant]:
    """Contestants whose place is within max_place, ordered by place then id."""
    qualified = [entry for entry in ranking if entry.place <= max_place]
    qualified.sort(key=lambda entry: (entry.place, entry.contestant.id))
    return [entry.contestant for entry in qualified]


class TwoWayResultKind(Enum):
    UNDECIDED = "undecided"
    DRAW = "draw"
    WINNER = "winner"


@dataclass(frozen=True)
class TwoWayOutcome:
    """Sport-neutral classification of a finished two-way contest result."""

    kind: TwoWayResultKind
    winner: Contestant | None = None


def classify_two_way_result(ranking: tuple[RankedEntry, ...]) -> TwoWayOutcome:
    """Classify a two-way ranking without producing display text."""
    if is_ex_aequo_first(ranking):
        return TwoWayOutcome(TwoWayResultKind.DRAW)
    winner = single_first_place(ranking)
    if winner is not None:
        return TwoWayOutcome(TwoWayResultKind.WINNER, winner)
    return TwoWayOutcome(TwoWayResultKind.UNDECIDED)
