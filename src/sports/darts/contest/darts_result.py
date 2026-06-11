from typing import Dict, Optional

from src.core.contestant import Contestant
from src.core.contest.result import Result


class DartsResult(Result):
    def __init__(
        self,
        winner: Optional[Contestant],
        sets_won: Dict[str, int],
        legs_won: Dict[str, int],
    ) -> None:
        self._winner = winner
        self.sets_won = sets_won.copy()
        self.legs_won = legs_won.copy()

    def is_finished(self) -> bool:
        return self._winner is not None

    def get_winner(self) -> Optional[Contestant]:
        return self._winner
