from __future__ import annotations

from typing import Protocol


class ContestantStats(Protocol):
    """Live per-subject statistics embedded in ContestState and updated via apply."""

    @property
    def subject_id(self) -> str: ...
