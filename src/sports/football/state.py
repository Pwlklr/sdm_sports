from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

from src.core.contest_state import ContestState
from src.sports.football.entities import (
    DisciplinaryRecord,
    MatchPeriod,
    PeriodKind,
)

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.sports.football.config import FootballMatchConfig


class MatchPhase(Enum):
    """The macro-stage of a football match."""

    REGULATION = "Regulation"
    EXTRA_TIME = "Extra Time"
    PENALTIES = "Penalties"
    COMPLETED = "Completed"


class FootballContestState(ContestState):
    """
    Manages the overarching state of a football match, delegating goal
    bookkeeping to MatchPeriod aggregates and cards to a DisciplinaryRecord.
    """

    def __init__(
        self,
        teams: List[Contestant],
        config: Optional[FootballMatchConfig] = None,
        number_of_halves: int = 2,
        half_length_minutes: int = 45,
        allow_draw: bool = True,
    ) -> None:
        super().__init__()
        if len(teams) != 2:
            raise ValueError("A football match requires exactly two sides.")

        self.teams = teams

        if config:
            self.number_of_halves = config.number_of_halves
            self.half_length_minutes = config.half_length_minutes
            self.allow_draw = config.allow_draw
            self.extra_time_halves = config.extra_time_halves
            self.extra_time_half_length = config.extra_time_half_length
            self.penalty_shootout_rounds = config.penalty_shootout_rounds
            yellows_per_dismissal = config.yellows_per_dismissal
        else:
            self.number_of_halves = number_of_halves
            self.half_length_minutes = half_length_minutes
            self.allow_draw = allow_draw
            self.extra_time_halves = 2
            self.extra_time_half_length = 15
            self.penalty_shootout_rounds = 5
            yellows_per_dismissal = 2

        self.scores: Dict[str, int] = {t.id: 0 for t in teams}
        self.penalty_scores: Dict[str, int] = {t.id: 0 for t in teams}
        self.penalty_attempts: Dict[str, int] = {t.id: 0 for t in teams}
        self.disciplinary = DisciplinaryRecord(yellows_per_dismissal)

        self.periods: List[MatchPeriod] = []
        self.current_period_idx: int = -1
        self.phase: MatchPhase = MatchPhase.REGULATION

        self.winner: Optional[Contestant] = None
        self.was_draw: bool = False
        self.decided_by: str = "regulation"
        self.is_completed: bool = False

    @property
    def current_period(self) -> Optional[MatchPeriod]:
        if 0 <= self.current_period_idx < len(self.periods):
            return self.periods[self.current_period_idx]
        return None

    def opponent_of(self, team: Contestant) -> Contestant:
        """Returns the other side; relies on the two-side invariant."""
        for candidate in self.teams:
            if candidate.id != team.id:
                return candidate
        return team

    def count_periods(self, kind: PeriodKind) -> int:
        return len([p for p in self.periods if p.kind == kind])

    def start_period(self, kind: PeriodKind = PeriodKind.REGULAR) -> MatchPeriod:
        """Opens a new period of the given kind and makes it current."""
        length = (
            self.half_length_minutes
            if kind == PeriodKind.REGULAR
            else self.extra_time_half_length
        )
        period = MatchPeriod(index=len(self.periods), length_minutes=length, kind=kind)
        self.periods.append(period)
        self.current_period_idx = len(self.periods) - 1
        return period

    def ensure_match_started(self) -> None:
        """Lazily kicks off the first regulation period on the first event."""
        if not self.periods and not self.is_completed:
            self.start_period(PeriodKind.REGULAR)

    @property
    def is_draw(self) -> bool:
        return self.scores[self.teams[0].id] == self.scores[self.teams[1].id]

    def leading_team(self) -> Optional[Contestant]:
        """Returns the side ahead on goals, or None if level."""
        first, second = self.teams[0], self.teams[1]
        if self.scores[first.id] > self.scores[second.id]:
            return first
        if self.scores[second.id] > self.scores[first.id]:
            return second
        return None

    def penalty_shootout_winner(self) -> Optional[Contestant]:
        """Resolves a shootout, honouring early clinches and sudden death."""
        first, second = self.teams[0], self.teams[1]
        attempts_a, attempts_b = (
            self.penalty_attempts[first.id],
            self.penalty_attempts[second.id],
        )
        score_a, score_b = (
            self.penalty_scores[first.id],
            self.penalty_scores[second.id],
        )
        rounds = self.penalty_shootout_rounds

        if attempts_a <= rounds and attempts_b <= rounds:
            remaining_a = max(rounds - attempts_a, 0)
            remaining_b = max(rounds - attempts_b, 0)
            if score_a - score_b > remaining_b:
                return first
            if score_b - score_a > remaining_a:
                return second

        if attempts_a == attempts_b and attempts_a >= rounds and score_a != score_b:
            return first if score_a > score_b else second

        return None
