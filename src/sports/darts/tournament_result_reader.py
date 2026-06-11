from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.core.contest.contest_result import ContestOutcome
from src.core.contest.result import Result
from src.core.contestant.models import Contestant
from src.core.tournament.match_outcome import HeadToHeadPoints
from src.core.tournament.result_reader import TournamentResultReader
from src.sports.darts.contest.darts_result import DartsResult

if TYPE_CHECKING:
    from src.core.contest.contest import Contest


class DartsTournamentResultReader(TournamentResultReader):
    def read_head_to_head(
        self, contest: Contest, result: Result
    ) -> Optional[HeadToHeadPoints]:
        sides = contest.contestants
        if len(sides) != 2:
            return None

        side_a, side_b = sides[0], sides[1]
        winner = _winner_from(result)
        if winner is None:
            return None
        if winner.id == side_a.id:
            return HeadToHeadPoints(side_a, side_b, 3, 0)
        if winner.id == side_b.id:
            return HeadToHeadPoints(side_a, side_b, 0, 3)
        return None

    def read_knockout_winner(
        self, contest: Contest, result: Result
    ) -> Optional[Contestant]:
        return _winner_from(result)

    def describe_result(self, contest: Contest, result: Result) -> str:
        winner = _winner_from(result)
        return f"wygral {winner.name}" if winner is not None else "zakonczony"


def _winner_from(result: Result) -> Optional[Contestant]:
    if isinstance(result, DartsResult):
        return result.get_winner()
    if isinstance(result, ContestOutcome) and not result.was_draw:
        return result.get_winner()
    return None
