from typing import Dict, Optional

from src.core.contest.contest_state import ContestState
from src.core.contestant import Contestant
from src.core.contest.result import Result
from src.sports.darts.contest.darts_contest_state import DartsContestState


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


def build_darts_result(state: ContestState) -> DartsResult:
    assert isinstance(state, DartsContestState)
    winner = state.player_by_id(state.winner_id) if state.winner_id else None
    return DartsResult(
        winner=winner,
        sets_won=state.sets_won,
        legs_won=state.legs_won,
    )
