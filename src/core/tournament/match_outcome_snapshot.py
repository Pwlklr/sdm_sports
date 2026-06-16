from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class RankedPlaceSnapshot:
    contestant_id: str
    place: int


@dataclass(frozen=True, kw_only=True)
class PointsDeltaSnapshot:
    contestant_id: str
    points: int
    wins: int = 0
    draws: int = 0
    losses: int = 0


@dataclass(frozen=True, kw_only=True)
class MatchOutcomeSnapshot:
    """Serializable outcome snapshot stored in tournament events for replay."""

    contest_id: str
    fingerprint: str
    winner_id: str | None
    ranking: tuple[RankedPlaceSnapshot, ...]
    points_deltas: tuple[PointsDeltaSnapshot, ...] = ()
    metrics_blob: dict[str, object] | None = None

    def same_as(self, other: MatchOutcomeSnapshot) -> bool:
        return self.fingerprint == other.fingerprint
