from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.core.contest.command import ReverseDecision
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event, EventReversed


@dataclass
class ReversalContext:
    """Shared state passed through the reversal CoR pipeline."""

    command: ReverseDecision
    state: ContestState
    history: list[Event]
    markers: list[EventReversed] = field(default_factory=list)


class ReversalHandler(ABC):
    """CoR link: contribute markers, then delegate to the successor."""

    def __init__(self, successor: ReversalHandler | None = None) -> None:
        self._successor = successor

    def handle(self, ctx: ReversalContext) -> None:
        self._contribute(ctx)
        if self._successor is not None:
            self._successor.handle(ctx)

    @abstractmethod
    def _contribute(self, ctx: ReversalContext) -> None:
        pass


class ValidateTargetExistsHandler(ReversalHandler):
    """Reject when the target event is not part of contest history."""

    def _contribute(self, ctx: ReversalContext) -> None:
        target_id = ctx.command.target_event_id
        if not any(event.event_id == target_id for event in ctx.history):
            raise ValueError(
                f"Event '{target_id}' is not part of this contest history."
            )


class RecordTargetHandler(ReversalHandler):
    """Always record a reversal marker for the command target."""

    def _contribute(self, ctx: ReversalContext) -> None:
        target_id = ctx.command.target_event_id
        if any(marker.target_event_id == target_id for marker in ctx.markers):
            return
        ctx.markers.append(
            EventReversed(
                target_event_id=target_id,
                reason=ctx.command.reason,
            )
        )


def default_reversal_chain() -> ReversalHandler:
    return ValidateTargetExistsHandler(RecordTargetHandler())
