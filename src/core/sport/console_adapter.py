from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.core.contest import Contest
from src.core.contest.command import Command
from src.core.sport.sport_descriptor import SportDescriptor


class ConsoleAdapter(ABC):
    """Console I/O: parse user input into commands and attach sport-specific views."""

    @property
    @abstractmethod
    def descriptor(self) -> SportDescriptor:
        pass

    @abstractmethod
    def collect_config(self) -> Any:
        pass

    @abstractmethod
    def attach_view(self, contest: Contest) -> None:
        pass

    @abstractmethod
    def get_start_command(self) -> Optional[Command]:
        pass

    @abstractmethod
    def get_input_prompt(self, contest: Contest) -> str:
        pass

    @abstractmethod
    def parse_command(self, user_input: str, contest: Contest) -> Optional[Command]:
        pass
