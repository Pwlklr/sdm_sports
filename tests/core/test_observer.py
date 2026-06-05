from src.core.observer import Subject, Observer


class MockObserver(Observer):
    def __init__(self):
        self.received_events = []

    def update(self, event):
        self.received_events.append(event)


class MockSubject(Subject):
    pass


def test_observer_registration_and_notification():
    """Verify that subjects correctly register, deregister, and notify observers."""
    subject = MockSubject()
    observer_a = MockObserver()
    observer_b = MockObserver()

    # Test Registration
    subject.attach(observer_a)
    subject.attach(observer_b)
    assert len(subject._observers) == 2

    # Test Notification
    test_event = {"type": "MATCH_STARTED", "payload": "123"}
    subject.notify(test_event)

    assert len(observer_a.received_events) == 1
    assert observer_a.received_events[0] == test_event
    assert len(observer_b.received_events) == 1

    # Test Deregistration
    subject.detach(observer_a)
    assert len(subject._observers) == 1

    subject.notify({"type": "MATCH_ENDED"})
    assert len(observer_a.received_events) == 1  # Should not increase
    assert len(observer_b.received_events) == 2  # Should increase
