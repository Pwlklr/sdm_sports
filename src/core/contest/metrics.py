from __future__ import annotations

from typing import Protocol


class SideMetrics(Protocol):
    """Side/contestant-level aggregates from a finished contest."""


class IndividualMetrics(Protocol):
    """Per-player aggregates nested inside side_metrics (team sports only)."""
