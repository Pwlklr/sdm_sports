from src.core.commands import Command, CommandInvoker


class MockCommand(Command):
    def __init__(self, value):
        self.value = value

    def execute(self):
        return f"Executed {self.value}"


def test_command_invoker_history_and_execution():
    """Verify the invoker executes commands and maintains history for potential undos/audits."""
    invoker = CommandInvoker()
    cmd1 = MockCommand("A")
    cmd2 = MockCommand("B")

    result1 = invoker.execute_command(cmd1)
    result2 = invoker.execute_command(cmd2)

    assert result1 == "Executed A"
    assert result2 == "Executed B"
    assert len(invoker.history) == 2
    assert invoker.history[0] == cmd1
    assert invoker.history[1] == cmd2
