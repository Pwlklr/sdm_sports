from __future__ import annotations

from src.core.tournament.blueprint import QualificationMode, QualificationRule
from src.core.tournament.phase_state import (
    BracketPhaseState,
    RoundRobinPhaseState,
)
from src.core.tournament.sport_tournament_profile import StandingsTiebreaker
from src.core.tournament.tournament_state import DefaultTournamentState


class PhaseQualifiers:
    """Resolves which contestants qualify from a completed phase."""

    def __init__(self, tiebreaker: StandingsTiebreaker) -> None:
        self._tiebreaker = tiebreaker

    def resolve(
        self,
        state: DefaultTournamentState,
        phase_id: str,
        rule: QualificationRule,
    ) -> tuple[str, ...]:
        ps = state.phase_states.get(phase_id)
        if ps is None:
            return ()

        if isinstance(ps, RoundRobinPhaseState):
            return self._rr_qualifiers(ps, rule)

        if isinstance(ps, BracketPhaseState):
            return self._bracket_qualifiers(ps, rule)

        return ()

    def _rr_qualifiers(
        self, ps: RoundRobinPhaseState, rule: QualificationRule
    ) -> tuple[str, ...]:
        mode = rule.mode

        if mode in (QualificationMode.TOP_N, QualificationMode.TOP_N_PER_GROUP):
            ids = list(ps.standings.keys())
            ordered = self._tiebreaker.order(ids, ps)
            return tuple(ordered[: rule.n])

        if mode == QualificationMode.WINNERS:
            ids = list(ps.standings.keys())
            ordered = self._tiebreaker.order(ids, ps)
            return tuple(ordered[: rule.n])

        if mode == QualificationMode.CHAMPION:
            ids = list(ps.standings.keys())
            ordered = self._tiebreaker.order(ids, ps)
            return (ordered[0],) if ordered else ()

        return ()

    def _bracket_qualifiers(
        self, ps: BracketPhaseState, rule: QualificationRule
    ) -> tuple[str, ...]:
        if rule.mode == QualificationMode.CHAMPION:
            for slot in reversed(ps.slots):
                if slot.winner_id:
                    return (slot.winner_id,)
            return ()

        if not ps.slots:
            return ()
        max_round = max((s.round_index for s in ps.slots), default=0)
        final_winners = [
            s.winner_id
            for s in ps.slots
            if s.round_index == max_round and s.winner_id is not None
        ]
        return tuple(final_winners[: rule.n])
