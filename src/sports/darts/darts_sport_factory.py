from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.contestant.models import Contestant, IndividualPlayer
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_result import build_darts_result
from src.sports.darts.contest.darts_rule_set import DartsRuleSet
from src.sports.darts.contest.darts_contest_state import DartsContestState


class DartsSportFactory:
    def create_contest(
        self, contestants: List[Contestant], config: DartsMatchConfig
    ) -> Contest:
        if not contestants:
            raise ValueError("A darts match requires at least one contestant.")
        for player in contestants:
            if not isinstance(player, IndividualPlayer):
                raise ValueError("Darts matches require IndividualPlayer contestants.")
        players = list(contestants)
        return Contest(
            contestants=contestants,
            initial_state=DartsContestState(players, config=config),
            ruleset=DartsRuleSet(config),
            result_factory=build_darts_result,
            state_factory=lambda: DartsContestState(players, config=config),
        )
