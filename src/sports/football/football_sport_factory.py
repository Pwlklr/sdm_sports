from __future__ import annotations

from typing import List, Optional

from src.core.contest import Contest
from src.core.contestant.models import Contestant, Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import build_football_result
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.squad_context import SquadContext
from src.sports.football.contest.state import FootballContestState


class FootballSportFactory:
    def create_contest(
        self,
        contestants: List[Contestant],
        config: FootballMatchConfig,
        squad_context: Optional[SquadContext] = None,
    ) -> Contest:
        if len(contestants) != 2:
            raise ValueError("A football match requires exactly two sides.")
        for side in contestants:
            if not isinstance(side, Team):
                raise ValueError("Football matches require Team contestants.")
        sides = list(contestants)
        return Contest(
            contestants=contestants,
            initial_state=FootballContestState(sides, config=config),
            ruleset=FootballRuleSet(config, squad_context=squad_context),
            result_factory=build_football_result,
            state_factory=lambda: FootballContestState(sides, config=config),
        )
