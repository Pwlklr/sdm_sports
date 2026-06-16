from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.tournament.ranking import describe_two_way_result
from src.core.tournament.tournament import Tournament


def active_matches(tournament: Tournament) -> List[Contest]:
    pending = tournament.pending_match_ids()
    return [
        tournament.get_match(mid)
        for mid in pending
        if tournament.get_match(mid) is not None
    ]


def standings_table(tournament: Tournament) -> List[str]:
    phase_id = tournament.active_phase_id()
    if phase_id is None:
        return ["(brak aktywnej fazy)"]
    return tournament.standings_view().standings_table(tournament.state, phase_id)


def _format_final_status(contest: Contest) -> str:
    if not contest.current_state.is_finished:
        return "oczekuje"
    try:
        result = contest.get_official_result()
    except ValueError:
        return "oczekuje"
    return describe_two_way_result(result.ranking())


def schedule_view(tournament: Tournament) -> List[str]:
    state = tournament.state
    phase_id = tournament.active_phase_id()
    if phase_id is None:
        return ["(brak aktywnej fazy)"]
    ps = state.phase_states.get(phase_id)
    if ps is None:
        return []
    lines: List[str] = []
    for index, fixture in enumerate(ps.fixtures, start=1):
        name_a = state.contestants.get(fixture.side_a_id, fixture.side_a_id)
        name_b = state.contestants.get(fixture.side_b_id, fixture.side_b_id)
        pairing = f"{name_a} vs {name_b}"
        contest = tournament.get_match(fixture.contest_id)
        status = _format_final_status(contest) if contest else "oczekuje"
        lines.append(f"{index}. {pairing} - {status}")
    return lines
