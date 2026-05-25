from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

from src.core.exceptions import UnsupportedContestEvent

if TYPE_CHECKING:
    from src.core.contest_event import ContestEvent
    from src.core.contest_state import ContestState



class RuleSet(ABC):
    """
    Validates in-match events based on the business rules specific to a given sport
    and tournament phase.
    """
    handlers: ClassVar[dict[type[ContestEvent], Handler]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is RuleSet:
            return
        handlers = getattr(cls, "handlers", None)
        if not isinstance(handlers, dict) or not handlers:
            raise TypeError(f"{cls.__name__} must define a non-empty handlers dict")

    def evaluate(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        try:
            handler = self.handlers[type(event)]
        except KeyError:
            raise UnsupportedContestEvent(type(event).__name__) from None
        return handler(self, event, state)


Handler: TypeAlias = Callable[
    ["RuleSet", "ContestEvent", "ContestState"],
    list["ContestEvent"],
]
