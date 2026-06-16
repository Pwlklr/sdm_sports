from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.scheduling_mode import SchedulingMode


class PhaseStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class PhaseSchedulingStatus(Enum):
    IN_PROGRESS = "in_progress"
    AWAITING_DRAW = "awaiting_draw"
    COMPLETED = "completed"


@dataclass(frozen=True, kw_only=True)
class Phase:
    id: str
    name: str
    format: PhaseFormat
    scheduling_mode: SchedulingMode
    match_config: Any
    status: PhaseStatus = PhaseStatus.PENDING
