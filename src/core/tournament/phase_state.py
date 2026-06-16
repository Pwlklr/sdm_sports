from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Protocol

from typing_extensions import Self

from src.core.tournament.event import TournamentProjectionEvent
from src.core.tournament.match_outcome_snapshot import (
    MatchOutcomeSnapshot,
    PointsDeltaSnapshot,
)
from src.core.tournament.phase import PhaseSchedulingStatus
from src.core.tournament.phase_format import PhaseFormat


@dataclass(frozen=True, kw_only=True)
class GroupStandingRow:
    contestant_id: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points: int = 0


@dataclass(frozen=True, kw_only=True)
class FixtureRef:
    contest_id: str
    slot_id: str
    side_a_id: str
    side_b_id: str
    round_index: int = 0


@dataclass(frozen=True, kw_only=True)
class BracketSlot:
    slot_id: str
    round_index: int
    side_a_id: str | None = None
    side_b_id: str | None = None
    winner_id: str | None = None
    contest_id: str | None = None


class PhaseState(Protocol):
    format: PhaseFormat

    @property
    def fixtures(self) -> tuple[FixtureRef, ...]: ...

    @property
    def outcomes(self) -> dict[str, MatchOutcomeSnapshot]: ...

    def apply(self, fact: TournamentProjectionEvent) -> Self: ...

    def reset(self) -> Self: ...

    def all_fixtures_resolved(self) -> bool: ...

    def pending_fixture_contest_ids(self) -> frozenset[str]: ...


@dataclass(frozen=True, kw_only=True)
class RoundRobinPhaseState:
    format: PhaseFormat = PhaseFormat.ROUND_ROBIN
    group_id: str = "default"
    standings: dict[str, GroupStandingRow] = field(default_factory=dict)
    fixtures: tuple[FixtureRef, ...] = ()
    outcomes: dict[str, MatchOutcomeSnapshot] = field(default_factory=dict)
    player_stats: dict[str, dict[str, object]] = field(default_factory=dict)

    def apply(self, fact: TournamentProjectionEvent) -> RoundRobinPhaseState:
        from src.core.tournament.event import (
            FixtureScheduled,
            MatchOutcomeRecorded,
        )

        if isinstance(fact, FixtureScheduled):
            fixture = FixtureRef(
                contest_id=fact.contest_id,
                slot_id=fact.slot_id,
                side_a_id=fact.side_a_id,
                side_b_id=fact.side_b_id,
                round_index=fact.round_index,
            )
            standings = dict(self.standings)
            for cid in (fact.side_a_id, fact.side_b_id):
                if cid not in standings:
                    standings[cid] = GroupStandingRow(contestant_id=cid)
            return replace(self, fixtures=self.fixtures + (fixture,), standings=standings)

        if isinstance(fact, MatchOutcomeRecorded):
            return self._apply_outcome(fact.snapshot)

        return self

    def _apply_outcome(self, snapshot: MatchOutcomeSnapshot) -> RoundRobinPhaseState:
        outcomes = dict(self.outcomes)
        outcomes[snapshot.contest_id] = snapshot
        standings: dict[str, GroupStandingRow] = {}
        player_stats: dict[str, dict[str, object]] = {}
        for fixture in self.fixtures:
            for cid in (fixture.side_a_id, fixture.side_b_id):
                if cid not in standings:
                    standings[cid] = GroupStandingRow(contestant_id=cid)
        for recorded in outcomes.values():
            for delta in recorded.points_deltas:
                row = standings.get(
                    delta.contestant_id,
                    GroupStandingRow(contestant_id=delta.contestant_id),
                )
                standings[delta.contestant_id] = GroupStandingRow(
                    contestant_id=delta.contestant_id,
                    played=row.played + 1,
                    wins=row.wins + delta.wins,
                    draws=row.draws + delta.draws,
                    losses=row.losses + delta.losses,
                    points=row.points + delta.points,
                )
            if recorded.metrics_blob:
                for pid, data in recorded.metrics_blob.items():
                    if isinstance(data, dict):
                        merged = dict(player_stats.get(pid, {}))
                        merged.update(data)
                        player_stats[pid] = merged
        return replace(
            self, outcomes=outcomes, standings=standings, player_stats=player_stats
        )

    def reset(self) -> RoundRobinPhaseState:
        return RoundRobinPhaseState(group_id=self.group_id)

    def all_fixtures_resolved(self) -> bool:
        if not self.fixtures:
            return False
        return all(f.contest_id in self.outcomes for f in self.fixtures)

    def pending_fixture_contest_ids(self) -> frozenset[str]:
        return frozenset(
            f.contest_id
            for f in self.fixtures
            if f.contest_id not in self.outcomes
        )


@dataclass(frozen=True, kw_only=True)
class BracketPhaseState:
    format: PhaseFormat
    scheduling_mode: object
    status: PhaseSchedulingStatus = PhaseSchedulingStatus.IN_PROGRESS
    slots: tuple[BracketSlot, ...] = ()
    fixtures: tuple[FixtureRef, ...] = ()
    outcomes: dict[str, MatchOutcomeSnapshot] = field(default_factory=dict)
    current_round_index: int = 0

    def apply(self, fact: TournamentProjectionEvent) -> BracketPhaseState:
        from src.core.tournament.event import (
            DrawPerformed,
            FixtureScheduled,
            MatchOutcomeRecorded,
            RoundCompleted,
        )
        from src.core.tournament.scheduling_mode import SchedulingMode

        if isinstance(fact, FixtureScheduled):
            fixture = FixtureRef(
                contest_id=fact.contest_id,
                slot_id=fact.slot_id,
                side_a_id=fact.side_a_id,
                side_b_id=fact.side_b_id,
                round_index=fact.round_index,
            )
            slots = list(self.slots)
            updated = False
            for i, slot in enumerate(slots):
                if slot.slot_id == fact.slot_id:
                    slots[i] = replace(
                        slot,
                        side_a_id=fact.side_a_id,
                        side_b_id=fact.side_b_id,
                        contest_id=fact.contest_id,
                    )
                    updated = True
                    break
            if not updated:
                slots.append(
                    BracketSlot(
                        slot_id=fact.slot_id,
                        round_index=fact.round_index,
                        side_a_id=fact.side_a_id,
                        side_b_id=fact.side_b_id,
                        contest_id=fact.contest_id,
                    )
                )
            return replace(
                self,
                fixtures=self.fixtures + (fixture,),
                slots=tuple(slots),
                status=PhaseSchedulingStatus.IN_PROGRESS,
            )

        if isinstance(fact, MatchOutcomeRecorded):
            state = replace(
                self,
                outcomes={**self.outcomes, fact.snapshot.contest_id: fact.snapshot},
            )
            slots = list(state.slots)
            for i, slot in enumerate(slots):
                if slot.contest_id == fact.snapshot.contest_id:
                    slots[i] = replace(slot, winner_id=fact.snapshot.winner_id)
                    break
            state = replace(state, slots=tuple(slots))
            return state

        if isinstance(fact, RoundCompleted):
            mode = self.scheduling_mode
            if mode == SchedulingMode.DRAW_BETWEEN_ROUNDS:
                return replace(
                    self,
                    current_round_index=fact.round_index + 1,
                    status=PhaseSchedulingStatus.AWAITING_DRAW,
                )
            return replace(self, current_round_index=fact.round_index + 1)

        if isinstance(fact, DrawPerformed):
            return replace(self, status=PhaseSchedulingStatus.IN_PROGRESS)

        return self

    def reset(self) -> BracketPhaseState:
        return BracketPhaseState(
            format=self.format,
            scheduling_mode=self.scheduling_mode,
        )

    def all_fixtures_resolved(self) -> bool:
        if not self.fixtures:
            return False
        return all(f.contest_id in self.outcomes for f in self.fixtures)

    def pending_fixture_contest_ids(self) -> frozenset[str]:
        return frozenset(
            f.contest_id
            for f in self.fixtures
            if f.contest_id not in self.outcomes
        )

    def round_complete(self, round_index: int) -> bool:
        round_fixtures = [f for f in self.fixtures if f.round_index == round_index]
        if not round_fixtures:
            return False
        return all(f.contest_id in self.outcomes for f in round_fixtures)
