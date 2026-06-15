from typing import Optional

from src.core.contest.event import Event
from src.core.contest.observer import Observer, Subject


class MockObserver(Observer):
    def __init__(self) -> None:
        self.update_calls = 0
        self.last_fact: Optional[Event] = None

    def update(self, subject: Subject, fact: Optional[Event] = None) -> None:
        self.update_calls += 1
        self.last_fact = fact


class MockSubject(Subject):
    pass


def test_observer_registration_and_notification() -> None:
    subject = MockSubject()
    observer = MockObserver()
    subject.attach(observer)
    subject.notify()
    assert observer.update_calls == 1
