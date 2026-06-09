from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

from src.core.contest.command import Command
from src.core.contest.event import Event

if TYPE_CHECKING:
    from src.core.contest.contest_state import ContestState


class RuleSet(ABC):
    """
    Pure decision engine: validates commands and derives follow-up facts.
    Never mutates contest state.
    """

    command_handlers: ClassVar[dict[type[Command], Handler]] = {}
    reaction_handlers: ClassVar[dict[type[Event], Handler]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is RuleSet:
            return
        cmd_handlers = getattr(cls, "command_handlers", None)
        react_handlers = getattr(cls, "reaction_handlers", None)
        if not isinstance(cmd_handlers, dict) or not isinstance(react_handlers, dict):
            raise TypeError(
                f"{cls.__name__} must define command_handlers and reaction_handlers dicts"
            )
        if not cmd_handlers and not react_handlers:
            raise TypeError(
                f"{cls.__name__} must register at least one command or reaction handler"
            )

    def decide(self, command: Command, state: ContestState) -> list[Event]:
        handler = self.command_handlers.get(type(command))
        if handler:
            return handler(self, command, state)
        return []

    def react(self, fact: Event, state: ContestState) -> list[Event]:
        handler = self.reaction_handlers.get(type(fact))
        if handler:
            return handler(self, fact, state)
        return []


Handler: TypeAlias = Callable[..., list[Event]]
