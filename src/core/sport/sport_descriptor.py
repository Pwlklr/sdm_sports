from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SportDescriptor:
    """Registry metadata for a sport module (identity + display label)."""

    id: str
    display_name: str
