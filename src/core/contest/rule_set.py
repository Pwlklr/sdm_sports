from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

from src.core.contest.command import Command, ReverseDecision
from src.core.contest.event import Event, EventReversed
from src.core.contest.reversal_chain import (
    ReversalContext,
    ReversalHandler,
    default_reversal_chain,
)

if TYPE_CHECKING:
    from src.core.contest.contest_state import ContestState


class RuleSet(ABC):
    """
    Pure decision engine: validates commands and derives follow-up facts.
    Never mutates contest state.

    Handler maps are merged across the whole MRO, so a concrete ruleset can be
    assembled from several mixins. Mixins contribute via ``_own_command_handlers``
    / ``_own_reaction_handlers`` (or plain ``command_handlers`` /
    ``reaction_handlers``). Two contributors registering the same key with a
    different handler raise a TypeError instead of silently overriding.
    """

    command_handlers: ClassVar[dict[type[Command], Handler]] = {}
    reaction_handlers: ClassVar[dict[type[Event], Handler]] = {}

    def __init__(
        self, reversal_chain: ReversalHandler | None = None
    ) -> None:
        self._reversal_chain = reversal_chain or default_reversal_chain()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is RuleSet:
            return

        merged_cmd: dict[type[Command], Handler] = {}
        merged_react: dict[type[Event], Handler] = {}
        for base in reversed(cls.__mro__):
            _collect_handlers(
                merged_cmd, base, ("command_handlers", "_own_command_handlers"), cls
            )
            _collect_handlers(
                merged_react, base, ("reaction_handlers", "_own_reaction_handlers"), cls
            )

        if not merged_cmd and not merged_react:
            raise TypeError(
                f"{cls.__name__} must register at least one command or reaction handler"
            )

        cls.command_handlers = merged_cmd
        cls.reaction_handlers = merged_react

    def decide(
        self,
        command: Command,
        state: ContestState,
        history: list[Event] | None = None,
    ) -> list[Event]:
        handler = self.command_handlers.get(type(command))
        if handler:
            return handler(self, command, state, history or [])
        return []

    def react(self, fact: Event, state: ContestState) -> list[Event]:
        handler = self.reaction_handlers.get(type(fact))
        if handler:
            return handler(self, fact, state)
        return []

    def decide_reversal(
        self,
        command: ReverseDecision,
        state: ContestState,
        history: list[Event],
    ) -> list[EventReversed]:
        ctx = ReversalContext(
            command=command,
            state=state,
            history=history,
        )
        self._reversal_chain.handle(ctx)
        return ctx.markers


Handler: TypeAlias = Callable[..., list[Event]]


def _collect_handlers(
    target: dict[Any, Handler],
    base: type,
    attr_names: tuple[str, ...],
    owner: type,
) -> None:
    for attr in attr_names:
        handlers = base.__dict__.get(attr)
        if not isinstance(handlers, dict):
            continue
        for key, handler in handlers.items():
            existing = target.get(key)
            if existing is not None and existing is not handler:
                raise TypeError(
                    f"{owner.__name__}: conflicting handler for {key.__name__} "
                    f"contributed by multiple mixins/bases."
                )
            target[key] = handler
