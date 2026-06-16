from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ContestantKind = Literal["individual", "team"]


@dataclass(frozen=True)
class SportDescriptor:
    """Registry metadata for a sport module (identity + display label)."""

    id: str
    display_name: str
    contestant_kind: ContestantKind = "individual"
