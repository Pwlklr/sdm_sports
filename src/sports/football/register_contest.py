from __future__ import annotations

from typing import Any

from src.core.contest.contest_factory import ContestAssembly, ContestFactory
from src.core.contestant.models import Contestant, Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_reversal import build_football_reversal_chain
from src.sports.football.contest.football_result_builder import FootballResultBuilder
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import create_football_contest_state
from src.sports.football.descriptor import FOOTBALL_SPORT


def _validate_football_setup(
    contestants: list[Contestant], config: FootballMatchConfig
) -> None:
    if len(contestants) != 2:
        raise ValueError("A football match requires exactly two sides.")
    for side in contestants:
        if not isinstance(side, Team):
            raise ValueError("Football matches require Team contestants.")
    if not isinstance(config, FootballMatchConfig):
        raise TypeError("Expected FootballMatchConfig.")


def _build_football_contest(
    contestants: list[Contestant],
    config: FootballMatchConfig,
    **options: Any,
) -> ContestAssembly:
    _validate_football_setup(contestants, config)
    suspended = options.get("suspended_player_ids")
    if suspended is not None and not isinstance(suspended, frozenset):
        suspended = frozenset(suspended)

    state = create_football_contest_state(
        contestants,
        config=config,
        suspended_player_ids=suspended,
    )
    ruleset = FootballRuleSet(
        config,
        reversal_chain=build_football_reversal_chain(),
    )
    result_builder = FootballResultBuilder(config=config)
    return ContestAssembly(state=state, ruleset=ruleset, result_builder=result_builder)


ContestFactory.register(FOOTBALL_SPORT.id, _build_football_contest)
