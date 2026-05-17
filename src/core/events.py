from abc import ABC
from datetime import datetime
import uuid
from typing import Optional

class DomainEvent(ABC):
    """
    The base abstraction representing any historical and immutable 
    state change throughout the system.
    """
    def __init__(self):
        self.event_id: str = str(uuid.uuid4())
        self.occurred_at: datetime = datetime.now()

class ContestEvent(DomainEvent):
    """
    Denotes events occurring during a specific match.
    """
    def __init__(self, competitor_id: Optional[str] = None, team_id: Optional[str] = None):
        super().__init__()
        self.competitor_id = competitor_id
        self.team_id = team_id