from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.tournament.phase import GroupStagePhase, TournamentPhase


def active_matches(phase: TournamentPhase) -> List[Contest]:
    """Scheduled matches in this phase that have not been played yet."""
    return [c for c in phase.contests if not c.current_state.is_completed]


def standings_table(phase: TournamentPhase) -> List[str]:
    if not isinstance(phase, GroupStagePhase) or not phase.standings:
        return ["(brak tabeli dla tej fazy)"]

    ranked = sorted(
        phase.standings.values(),
        key=lambda row: (row.points, row.wins, -row.losses),
        reverse=True,
    )
    lines = ["#  Druzyna                 M   W  R  P  Pkt"]
    for position, row in enumerate(ranked, start=1):
        lines.append(
            f"{position:<2} {row.contestant.name:<22} "
            f"{row.played:<3} {row.wins:<2} {row.draws:<2} {row.losses:<2} {row.points}"
        )
    return lines


def schedule_view(phase: TournamentPhase) -> List[str]:
    lines: List[str] = []
    for index, contest in enumerate(phase.contests, start=1):
        home = contest.home.name if contest.home is not None else "?"
        away = contest.away.name if contest.away is not None else "?"
        pairing = f"{home} (dom) vs {away} (wyjazd)"
        result = contest.official_result
        if result is None or not contest.current_state.is_completed:
            status = "oczekuje"
        else:
            winner = result.get_winner()
            status = f"wygral {winner.name}" if winner is not None else "remis"
        lines.append(f"{index}. {pairing} - {status}")
    return lines
