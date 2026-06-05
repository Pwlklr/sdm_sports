import pytest
from src.core.exceptions import DomainException, RuleViolationException


def test_domain_exception_base():
    """Ensure base domain exception can be raised with a correct message."""
    msg = "A core domain error occurred."
    with pytest.raises(DomainException) as exc_info:
        raise DomainException(msg)
    assert str(exc_info.value) == msg


def test_rule_violation_exception():
    """Ensure specific rule violations map to the exact offending action/participant."""
    msg = "Invalid checkout attempt."
    violator_id = "Player_1"

    with pytest.raises(RuleViolationException) as exc_info:
        raise RuleViolationException(msg, violator_id)

    assert str(exc_info.value) == f"{msg} (Violator: {violator_id})"
    assert exc_info.value.violator_id == violator_id
