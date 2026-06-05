import pytest
from src.core.exceptions import UnsupportedContestEvent


def test_unsupported_contest_event_exception():
    """Ensure the UnsupportedContestEvent can be raised and captures the message."""
    error_message = "Event 'InvalidThrow' is not supported in this context."

    with pytest.raises(UnsupportedContestEvent) as exc_info:
        raise UnsupportedContestEvent(error_message)

    # Verify the exception message is correctly stored and returned
    assert str(exc_info.value) == error_message
