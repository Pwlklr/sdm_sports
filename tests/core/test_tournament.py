from __future__ import annotations

import pytest

from src.core.contest import Contest
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.core.ruleset import RuleSet
from src.core.team import Team
from src.core.tournament_phase import TournamentPhase


class DummyState(ContestState):
    pass


class DummyEvent(ContestEvent):
    action_type: str

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self.action_type = action_type


class DummyRuleSet(RuleSet):
    handlers = {
        DummyEvent: lambda self, event, state: DummyRuleSet._on_dummy(
            self, event, state
        ),
    }

    def _on_dummy(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        if event.action_type == "END":
            state.is_final = True
        return []


def test_tournament_phase_observes_contest_completion():
    team_a = Team(team_id="T1", name="Team A")
    team_b = Team(team_id="T2", name="Team B")

    contest = Contest("C1", [team_a, team_b], DummyState(), DummyRuleSet())
    phase = TournamentPhase("Phase-1", DummyRuleSet())

    phase.add_contest(contest)

    assert phase.completed_contests == 0

    contest.process_event(DummyEvent("END"))

    assert phase.completed_contests == 1
