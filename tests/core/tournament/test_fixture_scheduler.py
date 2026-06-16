from __future__ import annotations

import itertools

from src.core.tournament.fixture_scheduler import BracketScheduler, RoundRobinScheduler
from src.core.tournament.scheduling_mode import SchedulingMode


def test_round_robin_scheduler_all_pairs() -> None:
    ids = ["a", "b", "c"]
    pairings = RoundRobinScheduler().initial_round(ids)
    assert len(pairings) == 3
    pairs = {tuple(sorted((p.side_a_id, p.side_b_id))) for p in pairings}
    assert pairs == {tuple(sorted(x)) for x in itertools.combinations(ids, 2)}


def test_bracket_scheduler_progressive_first_round() -> None:
    ids = [f"p{i}" for i in range(4)]
    pairings = BracketScheduler(SchedulingMode.PROGRESSIVE).initial_round(ids)
    assert len(pairings) == 2


def test_bracket_scheduler_next_round() -> None:
    scheduler = BracketScheduler(SchedulingMode.PROGRESSIVE)
    next_pairs = scheduler.next_round(
        ["a", "b"],
        round_index=1,
        winners_by_slot={"s0": "a", "s1": "b"},
    )
    assert len(next_pairs) == 1
    assert next_pairs[0].side_a_id == "a"
    assert next_pairs[0].side_b_id == "b"
