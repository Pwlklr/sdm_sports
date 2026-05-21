from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        """Called when the observed subject changes state."""
        pass


class Subject(ABC):
    def __init__(self) -> None:
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self) -> None:
        """Notifies all attached observers of a state change."""
        for observer in self._observers:
            observer.update(self)
