from __future__ import annotations

from abc import ABC, abstractmethod
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
        found = False
        for phase in self.phases:
            if found:
                return phase
            if phase.id == phase_id:
                found = True
        return None

    def first_phase(self) -> PhaseDefinition | None:
        if not self.phases:
            return None
        return self.phases[0]
