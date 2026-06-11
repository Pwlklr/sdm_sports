from __future__ import annotations

from typing import Any

from src.core.contest.contest_factory import ContestFactory
from src.core.contestant.models import Contestant
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_reversal import build_darts_reversal_chain
from src.sports.darts.contest.darts_rule_set import DartsRuleSet
from src.sports.darts.descriptor import DARTS_SPORT


def _build_darts_contest(
    contestants: list[Contestant],
    config: DartsMatchConfig,
    **_: Any,
) -> tuple[DartsContestState, DartsRuleSet]:
    state = DartsContestState(contestants, config=config)
    ruleset = DartsRuleSet(config, reversal_chain=build_darts_reversal_chain())
    return state, ruleset


ContestFactory.register(DARTS_SPORT.id, _build_darts_contest)
