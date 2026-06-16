from __future__ import annotations

from src.core.contest.event import Event, EventReversed
from src.core.contest.reversal_chain import ReversalContext, ReversalHandler
from src.sports.darts.contest.commands import RevokeDartThrow
from src.sports.darts.contest.events import DartScored, LegStarted, LegWon


def _append_marker(ctx: ReversalContext, target_event_id: str) -> None:
    if any(marker.target_event_id == target_event_id for marker in ctx.markers):
        return
    ctx.markers.append(
        EventReversed(
            target_event_id=target_event_id,
            reason=ctx.command.reason,
        )
    )


def _event_by_id(ctx: ReversalContext, event_id: str) -> Event | None:
    for event in ctx.history:
        if event.event_id == event_id:
            return event
    return None


class DartsLegIntegrityHandler(ReversalHandler):
    """Invalidate a leg outcome when an earlier dart in the same leg is revoked."""

    def _contribute(self, ctx: ReversalContext) -> None:
        if not isinstance(ctx.command, RevokeDartThrow):
            return

        target = _event_by_id(ctx, ctx.command.target_event_id)
        if not isinstance(target, DartScored):
            return

        target_index = next(
            i
            for i, event in enumerate(ctx.history)
            if event.event_id == target.event_id
        )

        for index, event in enumerate(ctx.history):
            if index <= target_index:
                continue
            if isinstance(event, LegStarted):
                break
            if isinstance(event, LegWon):
                if event.caused_by != target.event_id:
                    _append_marker(ctx, event.event_id)
                break


def build_darts_reversal_chain() -> ReversalHandler:
    from src.core.contest.reversal_chain import (
        RecordTargetHandler,
        ValidateTargetExistsHandler,
    )

    return ValidateTargetExistsHandler(DartsLegIntegrityHandler(RecordTargetHandler()))
