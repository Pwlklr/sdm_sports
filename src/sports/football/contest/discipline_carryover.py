from __future__ import annotations

from src.core.tournament.tournament_disciplinary_board import (
    TournamentDisciplinaryBoard,
)
from src.sports.football.contest.match_metrics_reader import FootballMatchMetricsReader

_reader = FootballMatchMetricsReader()


def accrue_suspensions(
    board: TournamentDisciplinaryBoard,
    result,
    yellow_threshold: int = 2,
) -> None:
    """Carry a finished match's cards into tournament-wide suspensions."""
    _reader.accrue_disciplinary(result, board, yellow_threshold=yellow_threshold)
