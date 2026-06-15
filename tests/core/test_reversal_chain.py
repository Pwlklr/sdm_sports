from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.command import ReverseDecision
from src.core.contest.event import Event, EventReversed
from src.core.contest.reversal_chain import (
    ReversalContext,
    ReversalHandler,
    RecordTargetHandler,
)
from tests.core.contest_test_support import MinimalContestState


@dataclass(frozen=True, kw_only=True)
class SampleFact(Event):
    pass


class CollectingHandler(ReversalHandler):
    def __init__(self, label: str, successor: ReversalHandler | None = None) -> None:
        super().__init__(successor)
        self.label = label
        self.seen: list[str] = []

    def _contribute(self, ctx: ReversalContext) -> None:
        self.seen.append(self.label)
        ctx.markers.append(
            EventReversed(
                target_event_id=f"{self.label}-{ctx.command.target_event_id}",
                reason=self.label,
            )
        )


def test_reversal_chain_runs_all_links_in_order() -> None:
    first = CollectingHandler("first")
    second = CollectingHandler("second", first)
    third = CollectingHandler("third", second)

    fact = SampleFact(event_id="aaa")
    ctx = ReversalContext(
        command=ReverseDecision(target_event_id="aaa"),
        state=MinimalContestState(),
        history=[fact],
    )
    third.handle(ctx)

    assert third.seen == ["third"]
    assert second.seen == ["second"]
    assert first.seen == ["first"]
    assert len(ctx.markers) == 3


def test_record_target_handler_appends_single_marker() -> None:
    fact = SampleFact(event_id="target")
    ctx = ReversalContext(
        command=ReverseDecision(target_event_id="target", reason="test"),
        state=MinimalContestState(),
        history=[fact],
    )
    RecordTargetHandler().handle(ctx)

    assert len(ctx.markers) == 1
    assert ctx.markers[0].target_event_id == "target"
    assert ctx.markers[0].reason == "test"
