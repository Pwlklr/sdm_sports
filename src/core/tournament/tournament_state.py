from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Protocol

from typing_extensions import Self

from src.core.tournament.event import TournamentProjectionEvent
from src.core.tournament.phase import Phase, PhaseStatus
from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.phase_state import (
    BracketPhaseState,
    PhaseState,
    RoundRobinPhaseState,
)


@dataclass(frozen=True, kw_only=True)
class DisciplineState:
    infractions: dict[str, list[str]] = field(default_factory=dict)
    suspensions: dict[str, int] = field(default_factory=dict)

    def apply(self, fact: TournamentProjectionEvent) -> DisciplineState:
        from src.core.tournament.event import (
            SuspensionIssued,
            SuspensionLifted,
            SuspensionServed,
        )

        if isinstance(fact, SuspensionIssued):
            suspensions = dict(self.suspensions)
            suspensions[fact.player_id] = max(
                suspensions.get(fact.player_id, 0), fact.matches
            )
            return replace(self, suspensions=suspensions)

        if isinstance(fact, SuspensionServed):
            current = self.suspensions.get(fact.player_id, 0)
            if current <= 0:
                return self
            suspensions = dict(self.suspensions)
            remaining = current - 1
            if remaining == 0:
                del suspensions[fact.player_id]
            else:
                suspensions[fact.player_id] = remaining
            return replace(self, suspensions=suspensions)

        if isinstance(fact, SuspensionLifted):
            if fact.player_id not in self.suspensions:
                return self
            suspensions = dict(self.suspensions)
            del suspensions[fact.player_id]
            return replace(self, suspensions=suspensions)

        return self

    def suspended_ids(self) -> frozenset[str]:
        return frozenset(pid for pid, n in self.suspensions.items() if n > 0)


class TournamentState(Protocol):
    @property
    def sport_id(self) -> str: ...

    @property
    def registration_open(self) -> bool: ...

    @property
    def contestants(self) -> dict[str, str]: ...

    @property
    def squads(self) -> dict[str, tuple[str, ...]]: ...

    @property
    def phases(self) -> tuple[Phase, ...]: ...

    @property
    def active_phase_id(self) -> str | None: ...

    @property
    def phase_states(self) -> dict[str, PhaseState]: ...

    @property
    def discipline(self) -> DisciplineState: ...

    @property
    def is_complete(self) -> bool: ...

    def apply(self, fact: TournamentProjectionEvent) -> Self: ...

    def reset(self) -> Self: ...


@dataclass(frozen=True, kw_only=True)
class DefaultTournamentState:
    sport_id: str
    blueprint_id: str
    registration_open: bool = False
    contestants: dict[str, str] = field(default_factory=dict)
    squads: dict[str, tuple[str, ...]] = field(default_factory=dict)
    phases: tuple[Phase, ...] = ()
    active_phase_id: str | None = None
    phase_states: dict[str, PhaseState] = field(default_factory=dict)
    discipline: DisciplineState = field(default_factory=DisciplineState)
    completed_phase_ids: tuple[str, ...] = ()
    qualifiers_by_phase: dict[str, tuple[str, ...]] = field(default_factory=dict)
    is_complete: bool = False
    champion_id: str | None = None

    def apply(self, fact: TournamentProjectionEvent) -> DefaultTournamentState:
        from src.core.tournament.event import (
            ContestantRegistered,
            FixtureScheduled,
            MatchOutcomeRecorded,
            PhaseCompleted,
            PhaseStarted,
            RegistrationClosed,
            RegistrationOpened,
            SquadRegistered,
            TournamentCompleted,
        )

        if isinstance(fact, RegistrationOpened):
            return replace(self, registration_open=True)

        if isinstance(fact, RegistrationClosed):
            return replace(self, registration_open=False)

        if isinstance(fact, ContestantRegistered):
            contestants = dict(self.contestants)
            contestants[fact.contestant_id] = fact.contestant_name
            return replace(self, contestants=contestants)

        if isinstance(fact, SquadRegistered):
            squads = dict(self.squads)
            squads[fact.contestant_id] = fact.player_ids
            return replace(self, squads=squads)

        if isinstance(fact, PhaseStarted):
            phases = list(self.phases)
            phase_states = dict(self.phase_states)
            for i, phase in enumerate(phases):
                if phase.id == fact.phase_id:
                    phases[i] = replace(phase, status=PhaseStatus.ACTIVE)
                    break
            if fact.format == PhaseFormat.ROUND_ROBIN:
                phase_states[fact.phase_id] = RoundRobinPhaseState()
            else:
                phase_states[fact.phase_id] = BracketPhaseState(
                    format=fact.format,
                    scheduling_mode=fact.scheduling_mode,
                )
            return replace(
                self,
                phases=tuple(phases),
                active_phase_id=fact.phase_id,
                phase_states=phase_states,
            )

        if isinstance(fact, FixtureScheduled):
            phase_states = dict(self.phase_states)
            ps = phase_states.get(fact.phase_id)
            if ps is not None:
                phase_states[fact.phase_id] = ps.apply(fact)
            return replace(self, phase_states=phase_states)

        if isinstance(fact, MatchOutcomeRecorded):
            phase_states = dict(self.phase_states)
            ps = phase_states.get(fact.phase_id)
            if ps is not None:
                phase_states[fact.phase_id] = ps.apply(fact)
            return replace(self, phase_states=phase_states)

        if isinstance(fact, PhaseCompleted):
            phases = list(self.phases)
            for i, phase in enumerate(phases):
                if phase.id == fact.phase_id:
                    phases[i] = replace(phase, status=PhaseStatus.COMPLETED)
                    break
            qualifiers = dict(self.qualifiers_by_phase)
            qualifiers[fact.phase_id] = fact.qualifier_ids
            completed = tuple(dict.fromkeys((*self.completed_phase_ids, fact.phase_id)))
            return replace(
                self,
                phases=tuple(phases),
                active_phase_id=None,
                completed_phase_ids=completed,
                qualifiers_by_phase=qualifiers,
            )

        if isinstance(fact, TournamentCompleted):
            return replace(self, is_complete=True, champion_id=fact.champion_id)

        discipline = self.discipline.apply(fact)
        if discipline is not self.discipline:
            phase_states = dict(self.phase_states)
            ps = phase_states.get(getattr(fact, "phase_id", ""))
            if ps is not None and hasattr(ps, "apply"):
                phase_states[getattr(fact, "phase_id")] = ps.apply(fact)
            return replace(
                self,
                discipline=discipline,
                phase_states=phase_states,
            )

        phase_states = dict(self.phase_states)
        phase_id = getattr(fact, "phase_id", None)
        if phase_id and phase_id in phase_states:
            phase_states[phase_id] = phase_states[phase_id].apply(fact)
            return replace(self, phase_states=phase_states)

        return self

    def reset(self) -> DefaultTournamentState:
        return DefaultTournamentState(
            sport_id=self.sport_id,
            blueprint_id=self.blueprint_id,
            phases=self.phases,
        )

    def active_phase(self) -> Phase | None:
        if self.active_phase_id is None:
            return None
        for phase in self.phases:
            if phase.id == self.active_phase_id:
                return phase
        return None

    def active_phase_state(self) -> PhaseState | None:
        if self.active_phase_id is None:
            return None
        return self.phase_states.get(self.active_phase_id)
