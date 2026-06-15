from __future__ import annotations

from typing import NoReturn


class CommandRejected(Exception):
    """Raised by a ruleset when a command is illegal in the current state."""

    def __init__(self, reason: str, code: str = "rejected") -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code


def reject(reason: str, code: str = "rejected") -> NoReturn:
    raise CommandRejected(reason, code)
