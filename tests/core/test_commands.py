from dataclasses import dataclass

from src.core.contest.command import Command


@dataclass(frozen=True, kw_only=True)
class ConcreteCommand(Command):
    label: str = "test"


def test_command_is_immutable_intent() -> None:
    command = ConcreteCommand()
    assert command.label == "test"
    assert command.issued_at is not None
