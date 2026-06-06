from typing import Dict, Optional
from src.core.result import Result
from src.core.contestant import Contestant

class DartsResult(Result):
    """
    Stores the final outcome and statistics of a Darts match.
    """
    def __init__(self, winner: Optional[Contestant], sets_won: Dict[str, int], legs_won: Dict[str, int]) -> None:
        self._winner = winner
        self.sets_won = sets_won.copy()
        self.legs_won = legs_won.copy()

    def is_finished(self) -> bool:
        return self._winner is not None

    def get_winner(self) -> Optional[Contestant]:
        return self._winner