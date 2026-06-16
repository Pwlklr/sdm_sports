from __future__ import annotations

from src.core.contest import Contest
from src.sports.darts.contest.darts_contest_state import DartsContestState


def format_darts_archived_match_lines(
    match_id: str, match: Contest, state: DartsContestState
) -> list[str]:
    desc = " vs ".join(pl.name for pl in state.players)
    lines = [
        f"\nMatch: {desc} (ID: {match_id[:8]})",
        (
            f"Format: {state.config.starting_score} Up | "
            f"Best of {state.config.sets_to_win_match} Sets"
        ),
        "Final Scoreboard:",
    ]
    for pl in state.players:
        lines.append(
            f"  - {pl.name}: {state.sets_won[pl.id]} Sets, "
            f"{state.legs_won[pl.id]} Legs"
        )
    return lines
