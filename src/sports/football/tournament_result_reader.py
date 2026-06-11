from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.core.contest.contest_result import ContestOutcome
from src.core.contest.result import Result
from src.core.contestant.models import Contestant
from src.core.tournament.match_outcome import HeadToHeadPoints
from src.core.tournament.result_reader import TournamentResultReader
from src.sports.football.contest.football_result import FootballResult

if TYPE_CHECKING:
    from src.core.contest.contest import Contest


class FootballTournamentResultReader(TournamentResultReader):
    def read_head_to_head(
        self, contest: Contest, result: Result
    ) -> Optional[HeadToHeadPoints]:
        sides = contest.contestants
        if len(sides) != 2:
            return None

        side_a, side_b = sides[0], sides[1]

        if isinstance(result, FootballResult):
            score_a = result.scores.get(side_a.id, 0)
            score_b = result.scores.get(side_b.id, 0)
            return _points_from_scores(side_a, side_b, score_a, score_b)

        if isinstance(result, ContestOutcome):
            return _points_from_outcome(side_a, side_b, result)

        return None

    def read_knockout_winner(
        self, contest: Contest, result: Result
    ) -> Optional[Contestant]:
        if isinstance(result, FootballResult):
            return result.get_winner()
        if isinstance(result, ContestOutcome):
            return result.get_winner()
        return None

    def describe_result(self, contest: Contest, result: Result) -> str:
        if isinstance(result, FootballResult):
            if result.was_draw:
                return "remis"
            winner = result.get_winner()
            return f"wygral {winner.name}" if winner is not None else "zakonczony"
        if isinstance(result, ContestOutcome):
            if result.was_draw:
                return "remis"
            winner = result.get_winner()
            return f"wygral {winner.name}" if winner is not None else "zakonczony"
        return "zakonczony"


def _points_from_scores(
    side_a: Contestant,
    side_b: Contestant,
    score_a: int,
    score_b: int,
) -> HeadToHeadPoints:
    if score_a == score_b:
        return HeadToHeadPoints(side_a, side_b, 1, 1)
    if score_a > score_b:
        return HeadToHeadPoints(side_a, side_b, 3, 0)
    return HeadToHeadPoints(side_a, side_b, 0, 3)


def _points_from_outcome(
    side_a: Contestant,
    side_b: Contestant,
    outcome: ContestOutcome,
) -> HeadToHeadPoints:
    if outcome.was_draw:
        return HeadToHeadPoints(side_a, side_b, 1, 1)
    winner = outcome.get_winner()
    if winner is None:
        return HeadToHeadPoints(side_a, side_b, 0, 0)
    if winner.id == side_a.id:
        return HeadToHeadPoints(side_a, side_b, 3, 0)
    return HeadToHeadPoints(side_a, side_b, 0, 3)
