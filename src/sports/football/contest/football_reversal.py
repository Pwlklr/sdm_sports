from __future__ import annotations

from src.core.contest.event import EventReversed
from src.core.contest.reversal_chain import ReversalContext, ReversalHandler
from src.core.shared.command_rejected import reject
from src.sports.football.contest.commands import RevokeCaution, VarOverturnGoal
from src.sports.football.contest.events import GoalScored, PlayerCautioned, PlayerDismissed
from src.sports.football.contest.football_contest_state import FootballContestState


def _append_marker(ctx: ReversalContext, target_event_id: str, reason: str | None = None) -> None:
    if any(marker.target_event_id == target_event_id for marker in ctx.markers):
        return
    ctx.markers.append(
        EventReversed(
            target_event_id=target_event_id,
            reason=reason or ctx.command.reason,
        )
    )


def _event_by_id(ctx: ReversalContext, event_id: str):
    for event in ctx.history:
        if event.event_id == event_id:
            return event
    return None


class FootballVarValidationHandler(ReversalHandler):
    """Validate VAR overturn applies only to goals in an active match."""

    def _contribute(self, ctx: ReversalContext) -> None:
        if not isinstance(ctx.command, VarOverturnGoal):
            return

        state = ctx.state
        if not isinstance(state, FootballContestState):
            reject("VAR jest dostepne tylko w meczu pilki noznej.")

        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna zastosowac VAR.")

        target = _event_by_id(ctx, ctx.command.target_event_id)
        if not isinstance(target, GoalScored):
            reject("VAR moze anulowac wylacznie gol.")


class FootballDisciplinaryInvalidationHandler(ReversalHandler):
    """Invalidate auto-dismissals when a caution loses validity."""

    def _contribute(self, ctx: ReversalContext) -> None:
        if not isinstance(ctx.command, RevokeCaution):
            return

        target = _event_by_id(ctx, ctx.command.target_event_id)
        if not isinstance(target, PlayerCautioned):
            reject("Mozna wycofac wylacznie zolta kartke.")

        offender_id = target.offender_id
        caution_ids = {
            event.event_id
            for event in ctx.history
            if isinstance(event, PlayerCautioned) and event.offender_id == offender_id
        }

        for event in ctx.history:
            if not isinstance(event, PlayerDismissed):
                continue
            if event.offender_id != offender_id:
                continue
            if event.caused_by not in caution_ids:
                continue
            _append_marker(ctx, event.event_id)


def build_football_reversal_chain() -> ReversalHandler:
    from src.core.contest.reversal_chain import (
        RecordTargetHandler,
        ValidateTargetExistsHandler,
    )

    return ValidateTargetExistsHandler(
        FootballVarValidationHandler(
            FootballDisciplinaryInvalidationHandler(RecordTargetHandler())
        )
    )
