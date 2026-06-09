from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.contestant.models import Contestant, Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import build_football_result
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import FootballContestState


class FootballSportFactory:
    def create_contest(
        self, contestants: List[Contestant], config: FootballMatchConfig
    ) -> Contest:
        if len(contestants) != 2:
            raise ValueError("A football match requires exactly two sides.")
        for side in contestants:
            if not isinstance(side, Team):
                raise ValueError("Football matches require Team contestants.")
        return Contest(
            contestants=contestants,
            initial_state=FootballContestState(list(contestants), config=config),
            ruleset=FootballRuleSet(config),
            result_factory=build_football_result,
        )
