from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, subject) -> None:
        """Called when the observed subject changes state."""
        pass

class Subject(ABC):
    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self) -> None:
        """Notifies all attached observers of a state change."""
        for observer in self._observers:
            observer.update(self)