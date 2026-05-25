from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contest import Contest


class MatchCommand(ABC):
    @abstractmethod
    def execute(self, contest: Contest) -> None:
        pass
