from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.tournament.phase import GroupStagePhase, TournamentPhase
from src.sports.darts.contest.darts_result import DartsResult
from src.sports.football.contest.football_result import FootballResult


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


def _format_final_status(contest: Contest) -> str:
    if not contest.current_state.is_completed:
        return "oczekuje"
    try:
        result = contest.get_final_result()
    except ValueError:
        return "oczekuje"

    if isinstance(result, FootballResult):
        if result.was_draw:
            return "remis"
        winner = result.get_winner()
        return f"wygral {winner.name}" if winner is not None else "zakonczony"

    if isinstance(result, DartsResult):
        winner = result.get_winner()
        return f"wygral {winner.name}" if winner is not None else "zakonczony"

    return "zakonczony"


def schedule_view(phase: TournamentPhase) -> List[str]:
    lines: List[str] = []
    for index, contest in enumerate(phase.contests, start=1):
        if len(contest.contestants) == 2:
            first, second = contest.contestants
            pairing = f"{first.name} (dom) vs {second.name} (wyjazd)"
        else:
            names = " vs ".join(c.name for c in contest.contestants) or "?"
            pairing = names
        status = _format_final_status(contest)
        lines.append(f"{index}. {pairing} - {status}")
    return lines
