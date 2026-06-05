from src.core.observer import Subject, Observer


class MockObserver(Observer):
    def __init__(self):
        self.update_calls = 0
        self.last_subject = None

    def update(self, subject: Subject) -> None:
        """Records that the update was called and stores the subject."""
        self.update_calls += 1
        self.last_subject = subject


class MockSubject(Subject):
    """A concrete subject for testing."""

    pass


def test_observer_registration_and_notification():
    """Verify that subjects correctly register and notify observers."""
    subject = MockSubject()
    observer_a = MockObserver()
    observer_b = MockObserver()

    # Test Registration
    subject.attach(observer_a)
    subject.attach(observer_b)

    # Assert observers were added
    assert len(subject._observers) == 2

    # Test idempotency: attaching the same observer shouldn't duplicate it
    subject.attach(observer_a)
    assert len(subject._observers) == 2

    # Test Notification
    subject.notify()

    # Assert both observers received the update with the correct subject reference
    assert observer_a.update_calls == 1
    assert observer_a.last_subject is subject

    assert observer_b.update_calls == 1
    assert observer_b.last_subject is subject
