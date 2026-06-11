from __future__ import annotations

from typing import Any

from src.core.contest.contest_factory import ContestFactory
from src.core.contestant.models import Contestant
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_reversal import build_football_reversal_chain
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import FootballContestState
from src.sports.football.descriptor import FOOTBALL_SPORT


def _build_football_contest(
    contestants: list[Contestant],
    config: FootballMatchConfig,
    **options: Any,
) -> tuple[FootballContestState, FootballRuleSet]:
    suspended = options.get("suspended_player_ids")
    if suspended is not None and not isinstance(suspended, frozenset):
        suspended = frozenset(suspended)

    state = FootballContestState(
        contestants,
        config=config,
        suspended_player_ids=suspended,
    )
    ruleset = FootballRuleSet(
        config,
        reversal_chain=build_football_reversal_chain(),
    )
    return state, ruleset


ContestFactory.register(FOOTBALL_SPORT.id, _build_football_contest)
