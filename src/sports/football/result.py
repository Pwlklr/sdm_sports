from typing import Dict, Optional

from src.core.contestant import Contestant
from src.core.result import Result


class FootballResult(Result):
    """
    Stores the final outcome and scoreline of a football match.
    """

    def __init__(
        self,
        winner: Optional[Contestant],
        scores: Dict[str, int],
        was_draw: bool,
        decided_by: str = "regulation",
    ) -> None:
        self._winner = winner
        self.scores = scores.copy()
        self.was_draw = was_draw
        self.decided_by = decided_by

    def is_finished(self) -> bool:
        return self._winner is not None or self.was_draw

    def get_winner(self) -> Optional[Contestant]:
        return self._winner
