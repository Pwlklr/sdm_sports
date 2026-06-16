from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import Command, ReverseDecision


@dataclass(frozen=True, kw_only=True)
class StartMatch(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class ThrowDart(Command):
    sector: int
    multiplier: int = 1


@dataclass(frozen=True, kw_only=True)
class CallOcheFault(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class RevokeDartThrow(ReverseDecision):
    pass


@dataclass(frozen=True, kw_only=True)
class AwardWalkover(Command):
    winner_id: str
    reason: str = "walkover"


__all__ = [
    "AwardWalkover",
    "CallOcheFault",
    "RevokeDartThrow",
    "StartMatch",
    "ThrowDart",
]
