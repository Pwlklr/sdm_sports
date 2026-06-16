from __future__ import annotations

from src.core.tournament.blueprint import QualificationMode, QualificationRule
from src.core.tournament.phase_state import BracketPhaseState, GroupStandingRow, RoundRobinPhaseState
from src.core.tournament.sport_tournament_profile import StandingsTiebreaker
from src.core.tournament.tournament_state import DefaultTournamentState


class PhaseStandingsView:
    def __init__(self, tiebreaker: StandingsTiebreaker) -> None:
        self._tiebreaker = tiebreaker

    def qualifiers(
        self,
        state: DefaultTournamentState,
        phase_id: str,
        rule: QualificationRule,
    ) -> tuple[str, ...]:
        ps = state.phase_states.get(phase_id)
        if ps is None:
            return ()

        if isinstance(ps, RoundRobinPhaseState):
            ids = list(ps.standings.keys())
            ordered = self._tiebreaker.order(ids, ps.standings)
            if rule.mode == QualificationMode.TOP_N:
                return tuple(ordered[: rule.n])
            return tuple(ordered[: rule.n])

        if isinstance(ps, BracketPhaseState):
            for slot in reversed(ps.slots):
                if slot.winner_id:
                    return (slot.winner_id,)
        return ()

    def standings_table(
        self, state: DefaultTournamentState, phase_id: str
    ) -> list[str]:
        ps = state.phase_states.get(phase_id)
        if not isinstance(ps, RoundRobinPhaseState):
            return []
        rows = sorted(
            ps.standings.values(),
            key=lambda r: (r.points, r.wins, -r.losses),
            reverse=True,
        )
        lines: list[str] = []
        for row in rows:
            name = state.contestants.get(row.contestant_id, row.contestant_id)
            lines.append(
                f"{name}: {row.points}pkt ({row.wins}W-{row.draws}R-{row.losses}L)"
            )
        return lines
