from __future__ import annotations

from enum import Enum


class SchedulingMode(Enum):
    FIXED = "fixed"
    PROGRESSIVE = "progressive"
    DRAW_BETWEEN_ROUNDS = "draw_between_rounds"
