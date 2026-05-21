from __future__ import annotations

from abc import ABC
from datetime import datetime
import uuid


class DomainEvent(ABC):
    """
    The base abstraction representing state change
    """
    event_id: str
    occurred_at: datetime

    def __init__(self) -> None:
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.now()
