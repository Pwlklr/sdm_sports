from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.contestant.models import Contestant


class SquadPolicy(ABC):
    """Sport-specific tournament squad validation rules."""

    @abstractmethod
    def validate_squad(
        self,
        contestant: Contestant,
        player_ids: tuple[str, ...],
    ) -> None:
        """Raise via reject() when the squad violates sport rules."""

    def default_squad(self, contestant: Contestant) -> tuple[str, ...] | None:
        """Optional auto-registration when a contestant joins the tournament."""
        return None


class PermissiveSquadPolicy(SquadPolicy):
    """Test helper: accepts any squad composition."""

    def validate_squad(
        self,
        contestant: Contestant,
        player_ids: tuple[str, ...],
    ) -> None:
        pass
