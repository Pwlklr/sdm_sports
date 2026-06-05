import pytest
from src.core.observer import Observer, Subject

class DummyObserver(Observer):
    def update(self, subject: Subject) -> None:
        pass

def test_observer_initial_state() -> None:
    observer = DummyObserver()
    assert observer is not None