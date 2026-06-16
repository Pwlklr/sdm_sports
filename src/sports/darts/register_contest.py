from __future__ import annotations

from typing import Any

from src.core.contest.contest_factory import ContestAssembly, ContestFactory
from src.core.contestant.models import Contestant, IndividualPlayer
from src.sports.darts.contest.darts_contest_state import create_darts_contest_state
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_reversal import build_darts_reversal_chain
from src.sports.darts.contest.darts_result_builder import DartsResultBuilder
from src.sports.darts.contest.darts_rule_set import DartsRuleSet
from src.sports.darts.descriptor import DARTS_SPORT


def _validate_darts_setup(
    contestants: list[Contestant], config: DartsMatchConfig
) -> None:
    if not contestants:
        raise ValueError("A match requires at least one contestant.")
    for player in contestants:
        if not isinstance(player, IndividualPlayer):
            raise ValueError("Darts matches require IndividualPlayer contestants.")
    if not isinstance(config, DartsMatchConfig):
        raise TypeError("Expected DartsMatchConfig.")


def _build_darts_contest(
    contestants: list[Contestant],
    config: DartsMatchConfig,
    **_: Any,
) -> ContestAssembly:
    _validate_darts_setup(contestants, config)
    state = create_darts_contest_state(contestants, config)
    ruleset = DartsRuleSet(config, reversal_chain=build_darts_reversal_chain())
    result_builder = DartsResultBuilder(config=config)
    return ContestAssembly(state=state, ruleset=ruleset, result_builder=result_builder)


ContestFactory.register(DARTS_SPORT.id, _build_darts_contest)
