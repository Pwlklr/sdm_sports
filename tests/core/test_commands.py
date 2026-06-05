from unittest.mock import MagicMock
from src.core.commands import MatchCommand
from src.core.contest import Contest


class ConcreteMatchCommand(MatchCommand):
    """A concrete implementation of MatchCommand for testing purposes."""

    def __init__(self):
        self.executed = False
        self.target_contest = None

    def execute(self, contest: Contest) -> None:
        self.executed = True
        self.target_contest = contest


def test_match_command_execution():
    """Verify that a concrete MatchCommand can be executed with a Contest."""
    # Arrange
    mock_contest = MagicMock(spec=Contest)
    command = ConcreteMatchCommand()

    # Act
    command.execute(mock_contest)

    # Assert
    assert command.executed is True
    assert command.target_contest is mock_contest
