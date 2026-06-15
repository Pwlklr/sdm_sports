from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.core.contest.event import Event


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject, fact: Optional[Event] = None) -> None:
        """Called when the observed subject publishes a fact."""
        pass


class Subject(ABC):
    def __init__(self) -> None:
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, fact: Optional[Event] = None) -> None:
        """Notifies all attached observers, optionally passing the triggering fact."""
        for observer in self._observers:
            observer.update(self, fact)
