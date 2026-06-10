from __future__ import annotations

from src.core.tournament.tournament_disciplinary_board import (
    TournamentDisciplinaryBoard,
)
from src.sports.football.contest.state import FootballContestState

YELLOW_SUSPENSION_THRESHOLD = 2


def accrue_suspensions(
    board: TournamentDisciplinaryBoard,
    state: FootballContestState,
    yellow_threshold: int = YELLOW_SUSPENSION_THRESHOLD,
) -> None:
    """Carry a finished match's cards into tournament-wide suspensions.

    - a dismissal (red card) suspends the player for the next match
    - cautions accumulate across matches; every ``yellow_threshold`` cautions adds a suspension
    """
    disciplinary = state.disciplinary

    for offender_id in disciplinary.dismissed:
        board.suspend(offender_id, 1)

    for player_id, yellows in disciplinary.yellow_cards.items():
        for _ in range(yellows):
            board.log_infraction_id(player_id, "yellow")
        total = board.infraction_count(player_id, "yellow")
        if total >= yellow_threshold:
            board.suspend(player_id, 1)
            board.log_infraction_id(player_id, "yellow_suspension_served")
            for _ in range(total):
                board.records[player_id].remove("yellow")
