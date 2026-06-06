from typing import List, Dict, Any, Optional
from src.core.contestant import Contestant
from src.core.contest import Contest
from src.core.tournament_event import (
    TournamentEvent, RegistrationOpened, PlayerRegistered, 
    RegistrationClosed, MatchScheduled
)

class TournamentRegistration:
    """Manages the registration phase of a tournament."""
    def __init__(self) -> None:
        self.is_open: bool = False
        self._contestants: List[Contestant] = []

    @property
    def registered_contestants(self) -> List[Contestant]:
        return self._contestants.copy()

    def open_registration(self) -> List[TournamentEvent]:
        self.is_open = True
        return [RegistrationOpened()]

    def register(self, contestant: Contestant) -> List[TournamentEvent]:
        if not self.is_open:
            raise ValueError("Cannot register: Registration is not open.")
        if contestant in self._contestants:
            raise ValueError(f"Contestant {contestant.display_name} is already registered.")
        
        self._contestants.append(contestant)
        return [PlayerRegistered(contestant)]

    def close_registration(self) -> List[TournamentEvent]:
        self.is_open = False
        return [RegistrationClosed()]


class TournamentScheduler:
    """Manages the queue and scheduling of matches."""
    def __init__(self) -> None:
        self._match_queue: List[Contest] = []

    @property
    def pending_matches(self) -> List[Contest]:
        return self._match_queue.copy()

    def schedule_match(self, match: Contest) -> List[TournamentEvent]:
        self._match_queue.append(match)
        return [MatchScheduled(match)]

    def pop_next_match(self) -> Optional[Contest]:
        """Retrieves and removes the next match from the queue."""
        if self._match_queue:
            return self._match_queue.pop(0)
        return None


class TournamentDisciplinaryBoard:
    """
    Tracks tournament-wide infractions (e.g., Yellow Card accumulation in Football,
    or severe Oche Fault accumulation in Darts).
    """
    def __init__(self) -> None:
        # Maps Contestant ID to a list of recorded violations/penalties
        self.records: Dict[str, List[Any]] = {}

    def log_infraction(self, contestant: Contestant, infraction: Any) -> None:
        if contestant.id not in self.records:
            self.records[contestant.id] = []
        self.records[contestant.id].append(infraction)