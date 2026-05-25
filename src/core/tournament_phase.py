from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.observer import Observer, Subject

if TYPE_CHECKING:
    from src.core.contest import Contest
    from src.core.ruleset import RuleSet


class TournamentPhase(Observer):
    """
    Represents a specific stage of the tournament that organizes matches
    according to assigned rules.
    """

    phase_id: str
    ruleset: RuleSet
    contests: list[Contest]
    completed_contests: int

    def __init__(
        self,
        phase_id: str,
        ruleset: RuleSet,
        contests: list[Contest] | None = None,
    ) -> None:
        self.phase_id = phase_id
        self.ruleset = ruleset
        self.contests = contests if contests is not None else []
        self.completed_contests = 0

    def add_contest(self, contest: Contest) -> None:
        self.contests.append(contest)
        contest.attach(self)

    def update(self, subject: Subject) -> None:
        from src.core.contest import Contest

        if isinstance(subject, Contest) and subject.current_state.is_final:
            self.completed_contests += 1
