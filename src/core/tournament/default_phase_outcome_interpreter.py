from __future__ import annotations

import hashlib
import json

from src.core.contest.contest_result import ContestResult
from src.core.tournament.match_outcome_snapshot import (
    MatchOutcomeSnapshot,
    PointsDeltaSnapshot,
    RankedPlaceSnapshot,
)
from src.core.tournament.phase_outcome_interpreter import PhaseOutcomeInterpreter
from src.core.tournament.ranking import head_to_head_points, single_first_place


class DefaultPhaseOutcomeInterpreter(PhaseOutcomeInterpreter):
    def interpret(self, contest_id: str, result: ContestResult) -> MatchOutcomeSnapshot:
        ranking = result.ranking()
        ranked = tuple(
            RankedPlaceSnapshot(contestant_id=e.contestant.id, place=e.place)
            for e in ranking
        )
        winner = single_first_place(ranking)
        points_deltas: list[PointsDeltaSnapshot] = []
        if len(ranking) == 2:
            a, b = ranking[0].contestant, ranking[1].contestant
            pa, pb = head_to_head_points(a, b, ranking)
            wa, da, la = (1, 0, 0) if pa > pb else (0, 1, 0) if pa == pb else (0, 0, 1)
            wb, db, lb = (1, 0, 0) if pb > pa else (0, 1, 0) if pb == pa else (0, 0, 1)
            points_deltas = [
                PointsDeltaSnapshot(
                    contestant_id=a.id, points=pa, wins=wa, draws=da, losses=la
                ),
                PointsDeltaSnapshot(
                    contestant_id=b.id, points=pb, wins=wb, draws=db, losses=lb
                ),
            ]
        fingerprint = _fingerprint(contest_id, ranked, winner)
        return MatchOutcomeSnapshot(
            contest_id=contest_id,
            fingerprint=fingerprint,
            winner_id=winner.id if winner else None,
            ranking=ranked,
            points_deltas=tuple(points_deltas),
        )


def _fingerprint(
    contest_id: str,
    ranking: tuple[RankedPlaceSnapshot, ...],
    winner_id: object,
) -> str:
    payload = {
        "contest_id": contest_id,
        "ranking": [(r.contestant_id, r.place) for r in ranking],
        "winner_id": getattr(winner_id, "id", winner_id),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
