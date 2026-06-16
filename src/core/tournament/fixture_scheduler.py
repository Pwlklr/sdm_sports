from __future__ import annotations

import itertools
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.tournament.scheduling_mode import SchedulingMode


@dataclass(frozen=True, kw_only=True)
class ScheduledPairing:
    slot_id: str
    side_a_id: str
    side_b_id: str
    round_index: int = 0


class FixtureScheduler(ABC):
    @abstractmethod
    def initial_round(
        self, contestant_ids: list[str], *, round_index: int = 0
    ) -> list[ScheduledPairing]:
        pass

    @abstractmethod
    def next_round(
        self,
        contestant_ids: list[str],
        *,
        round_index: int,
        winners_by_slot: dict[str, str],
    ) -> list[ScheduledPairing]:
        pass


class RoundRobinScheduler(FixtureScheduler):
    def __init__(self, rounds: int = 1) -> None:
        self._rounds = rounds

    def initial_round(
        self, contestant_ids: list[str], *, round_index: int = 0
    ) -> list[ScheduledPairing]:
        pairings: list[ScheduledPairing] = []
        for r in range(self._rounds):
            for a, b in itertools.combinations(contestant_ids, 2):
                pairings.append(
                    ScheduledPairing(
                        slot_id=str(uuid.uuid4()),
                        side_a_id=a,
                        side_b_id=b,
                        round_index=r,
                    )
                )
        return pairings

    def next_round(
        self,
        contestant_ids: list[str],
        *,
        round_index: int,
        winners_by_slot: dict[str, str],
    ) -> list[ScheduledPairing]:
        return []


def _bracket_rounds(n: int) -> list[int]:
    """Return match counts per round for single elimination."""
    rounds: list[int] = []
    remaining = n
    while remaining > 1:
        rounds.append(remaining // 2)
        remaining = remaining // 2
    return rounds


class BracketScheduler(FixtureScheduler):
    def __init__(self, scheduling_mode: SchedulingMode) -> None:
        self._mode = scheduling_mode

    def initial_round(
        self, contestant_ids: list[str], *, round_index: int = 0
    ) -> list[ScheduledPairing]:
        n = len(contestant_ids)
        if n < 2:
            return []
        rounds = _bracket_rounds(n)
        if self._mode == SchedulingMode.FIXED:
            return self._fixed_all_rounds(contestant_ids, rounds)
        return self._seeded_round(contestant_ids, round_index)

    def _seeded_round(
        self, contestant_ids: list[str], round_index: int
    ) -> list[ScheduledPairing]:
        if round_index != 0:
            return []
        pairings: list[ScheduledPairing] = []
        ordered = list(contestant_ids)
        half = len(ordered) // 2
        for i in range(half):
            pairings.append(
                ScheduledPairing(
                    slot_id=f"r{round_index}-s{i}",
                    side_a_id=ordered[i],
                    side_b_id=ordered[-1 - i],
                    round_index=round_index,
                )
            )
        return pairings

    def _fixed_all_rounds(
        self, contestant_ids: list[str], rounds: list[int]
    ) -> list[ScheduledPairing]:
        pairings: list[ScheduledPairing] = []
        slots_per_round: list[list[str]] = []
        current = [
            f"TBD-{i}"
            for i in range(2 ** int(math.ceil(math.log2(len(contestant_ids)))))
        ]
        for i, c in enumerate(contestant_ids):
            if i < len(current):
                current[i] = c
        layer = current
        for r, count in enumerate(rounds):
            next_layer: list[str] = []
            round_slots: list[str] = []
            for m in range(count):
                slot_id = f"r{r}-s{m}"
                round_slots.append(slot_id)
                a = layer[m * 2] if m * 2 < len(layer) else f"TBD-{m}a"
                b = layer[m * 2 + 1] if m * 2 + 1 < len(layer) else f"TBD-{m}b"
                if r == 0:
                    if not a.startswith("TBD") and not b.startswith("TBD"):
                        pairings.append(
                            ScheduledPairing(
                                slot_id=slot_id,
                                side_a_id=a,
                                side_b_id=b,
                                round_index=r,
                            )
                        )
                next_layer.extend([f"W-{slot_id}-a", f"W-{slot_id}-b"])
            slots_per_round.append(round_slots)
            layer = next_layer
        if not pairings:
            return self._seeded_round(contestant_ids, 0)
        return pairings

    def next_round(
        self,
        contestant_ids: list[str],
        *,
        round_index: int,
        winners_by_slot: dict[str, str],
    ) -> list[ScheduledPairing]:
        winners = list(winners_by_slot.values())
        if len(winners) < 2:
            return []
        pairings: list[ScheduledPairing] = []
        for i in range(0, len(winners) - 1, 2):
            if i + 1 >= len(winners):
                break
            pairings.append(
                ScheduledPairing(
                    slot_id=f"r{round_index}-s{i // 2}",
                    side_a_id=winners[i],
                    side_b_id=winners[i + 1],
                    round_index=round_index,
                )
            )
        return pairings


class DoubleEliminationScheduler(BracketScheduler):
    def __init__(self) -> None:
        super().__init__(SchedulingMode.PROGRESSIVE)
