from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.scheduling_mode import SchedulingMode


class QualificationMode(Enum):
    TOP_N = "top_n"
    TOP_N_PER_GROUP = "top_n_per_group"
    WINNERS = "winners"
    CHAMPION = "champion"


@dataclass(frozen=True, kw_only=True)
class QualificationRule:
    mode: QualificationMode
    n: int = 1


@dataclass(frozen=True, kw_only=True)
class PhaseDefinition:
    id: str
    name: str
    format: PhaseFormat
    scheduling_mode: SchedulingMode
    match_config: Any
    qualification: QualificationRule
    requires: str | None = None
    group_count: int = 1

    @classmethod
    def round_robin(
        cls,
        phase_id: str,
        *,
        name: str = "",
        match_config: Any = None,
        qualifies: int = 1,
        requires: str | None = None,
        group_count: int = 1,
    ) -> PhaseDefinition:
        return cls(
            id=phase_id,
            name=name or phase_id,
            format=PhaseFormat.ROUND_ROBIN,
            scheduling_mode=SchedulingMode.FIXED,
            match_config=match_config,
            qualification=QualificationRule(mode=QualificationMode.TOP_N, n=qualifies),
            requires=requires,
            group_count=group_count,
        )

    @classmethod
    def knockout(
        cls,
        phase_id: str,
        *,
        name: str = "",
        match_config: Any = None,
        requires: str | None = None,
        double_elimination: bool = False,
    ) -> PhaseDefinition:
        fmt = (
            PhaseFormat.DOUBLE_ELIMINATION
            if double_elimination
            else PhaseFormat.SINGLE_ELIMINATION
        )
        return cls(
            id=phase_id,
            name=name or phase_id,
            format=fmt,
            scheduling_mode=SchedulingMode.PROGRESSIVE,
            match_config=match_config,
            qualification=QualificationRule(mode=QualificationMode.CHAMPION),
            requires=requires,
        )


@dataclass(frozen=True, kw_only=True)
class TournamentBlueprint:
    id: str
    name: str
    phases: tuple[PhaseDefinition, ...]

    def get_phase(self, phase_id: str) -> PhaseDefinition | None:
        for phase in self.phases:
            if phase.id == phase_id:
                return phase
        return None

    def next_phase_after(self, phase_id: str) -> PhaseDefinition | None:
        """Return the first phase whose ``requires`` points to ``phase_id``.

        Falls back to the next-in-sequence phase when no explicit dependency
        is declared (for single-phase blueprints or sequential chains without
        ``requires``).
        """
        # Prefer explicit requirement chain over positional order.
        for phase in self.phases:
            if phase.requires == phase_id:
                return phase
        # Fallback: next in declaration order.
        found = False
        for phase in self.phases:
            if found:
                return phase
            if phase.id == phase_id:
                found = True
        return None

    def phases_requiring(self, phase_id: str) -> tuple[PhaseDefinition, ...]:
        """All phases that explicitly depend on ``phase_id`` completing first."""
        return tuple(p for p in self.phases if p.requires == phase_id)

    def validate(self) -> list[str]:
        """Return a list of validation error messages (empty = valid)."""
        errors: list[str] = []
        ids = {p.id for p in self.phases}
        for p in self.phases:
            if p.requires is not None and p.requires not in ids:
                errors.append(f"Phase '{p.id}' requires unknown phase '{p.requires}'")
        return errors

    def first_phase(self) -> PhaseDefinition | None:
        if not self.phases:
            return None
        return self.phases[0]
