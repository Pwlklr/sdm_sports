from typing import List, Optional

from src.core.contest.contest import Contest
from src.core.tournament.event import MatchScheduled, TournamentEvent


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
        if self._match_queue:
            return self._match_queue.pop(0)
        return None
