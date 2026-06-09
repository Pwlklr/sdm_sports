from typing import Optional

from src.core.contest.event import Event
from src.core.contest.observer import Observer, Subject


class MockObserver(Observer):
    def __init__(self) -> None:
        self.update_calls = 0
        self.last_subject: Optional[Subject] = None
        self.last_fact: Optional[Event] = None

    def update(self, subject: Subject, fact: Optional[Event] = None) -> None:
        self.update_calls += 1
        self.last_subject = subject
        self.last_fact = fact


class MockSubject(Subject):
    pass


def test_observer_registration_and_notification() -> None:
    subject = MockSubject()
    observer_a = MockObserver()
    observer_b = MockObserver()

    subject.attach(observer_a)
    subject.attach(observer_b)
    assert len(subject._observers) == 2

    subject.attach(observer_a)
    assert len(subject._observers) == 2

    subject.notify()
    assert observer_a.update_calls == 1
    assert observer_a.last_subject is subject
    assert observer_b.update_calls == 1


def test_observer_detach() -> None:
    subject = MockSubject()
    observer = MockObserver()
    subject.attach(observer)
    subject.detach(observer)
    subject.notify()
    assert observer.update_calls == 0
