from __future__ import annotations

from src.core.domain_event import DomainEvent


class ContestEvent(DomainEvent):
    """
    Denotes events occurring during a specific match.
    """
    competitor_id: str | None
    team_id: str | None

    def __init__(
        self,
        competitor_id: str | None = None,
        team_id: str | None = None,
    ) -> None:
        super().__init__()
        self.competitor_id = competitor_id
        self.team_id = team_id
