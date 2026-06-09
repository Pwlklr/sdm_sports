#!/usr/bin/env python3
"""Rewrite imports after module split and remove obsolete flat files."""
from __future__ import annotations

import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]

REPLACEMENTS: list[tuple[str, str]] = [
    ("from src.core.command import", "from src.core.contest.command import"),
    ("from src.core.contest_event import", "from src.core.contest.event import"),
    ("from src.core.contest_state import", "from src.core.contest.state import"),
    ("from src.core.result import", "from src.core.contest.result import"),
    ("from src.core.ruleset import", "from src.core.contest.ruleset import"),
    ("from src.core.observer import", "from src.core.contest.observer import"),
    ("from src.core.tournament_event import", "from src.core.tournament.event import"),
    ("from src.core.tournament_state import", "from src.core.tournament.state import"),
    ("from src.core.tournament_phase import", "from src.core.tournament.phase import"),
    ("from src.core.tournament_policy import", "from src.core.tournament.policy import"),
    ("from src.core.draw_strategies import", "from src.core.tournament.draw import"),
    ("from src.core.sport_factory import", "from src.core.sport.factory import"),
    ("from src.core.console_adapter import", "from src.core.sport.adapter import"),
    ("from src.core.engine import", "from src.core.system.engine import"),
    ("from src.core.exceptions import", "from src.core.shared.exceptions import"),
    ("from src.core.domain_event import", "from src.core.shared.domain_event import"),
    ("from src.sports.football.commands import", "from src.sports.football.contest.commands import"),
    ("from src.sports.football.events import", "from src.sports.football.contest.events import"),
    ("from src.sports.football.state import", "from src.sports.football.contest.state import"),
    ("from src.sports.football.ruleset import", "from src.sports.football.contest.ruleset import"),
    ("from src.sports.football.result import", "from src.sports.football.contest.result import"),
    ("from src.sports.football.config import", "from src.sports.football.contest.config import"),
    ("from src.sports.football.entities import", "from src.sports.football.contest.entities import"),
    ("from src.sports.football.plugin import", "from src.sports.football.adapter import"),
    ("from src.sports.football.player import", "from src.sports.football.contestant.player import"),
    ("from src.sports.darts.commands import", "from src.sports.darts.contest.commands import"),
    ("from src.sports.darts.events import", "from src.sports.darts.contest.events import"),
    ("from src.sports.darts.state import", "from src.sports.darts.contest.state import"),
    ("from src.sports.darts.ruleset import", "from src.sports.darts.contest.ruleset import"),
    ("from src.sports.darts.result import", "from src.sports.darts.contest.result import"),
    ("from src.sports.darts.config import", "from src.sports.darts.contest.config import"),
    ("from src.sports.darts.entities import", "from src.sports.darts.contest.entities import"),
    ("from src.sports.darts.plugin import", "from src.sports.darts.adapter import"),
    ("from src.sports.darts.player import", "from src.sports.darts.contestant.player import"),
    ("from src.console.football_view import", "from src.sports.football.console.view import"),
    ("from src.console.darts_view import", "from src.sports.darts.console.view import"),
]

AGGREGATE_IMPORT = (
    "from src.core.tournament_aggregates import (\n"
    "    TournamentRegistration,\n"
    "    TournamentScheduler,\n"
    "    TournamentDisciplinaryBoard,\n"
    ")"
)
AGGREGATE_REPLACEMENT = (
    "from src.core.tournament.registration import TournamentRegistration\n"
    "from src.core.tournament.scheduler import TournamentScheduler\n"
    "from src.core.tournament.disciplinary import TournamentDisciplinaryBoard"
)

OBSOLETE = [
    "src/core/command.py",
    "src/core/contest_event.py",
    "src/core/contest_state.py",
    "src/core/contest.py",
    "src/core/result.py",
    "src/core/ruleset.py",
    "src/core/observer.py",
    "src/core/contestant.py",
    "src/core/tournament.py",
    "src/core/tournament_event.py",
    "src/core/tournament_state.py",
    "src/core/tournament_phase.py",
    "src/core/tournament_policy.py",
    "src/core/tournament_aggregates.py",
    "src/core/draw_strategies.py",
    "src/core/sport_factory.py",
    "src/core/console_adapter.py",
    "src/core/engine.py",
    "src/core/exceptions.py",
    "src/core/domain_event.py",
    "src/sports/football/commands.py",
    "src/sports/football/events.py",
    "src/sports/football/state.py",
    "src/sports/football/ruleset.py",
    "src/sports/football/result.py",
    "src/sports/football/config.py",
    "src/sports/football/entities.py",
    "src/sports/football/plugin.py",
    "src/sports/football/player.py",
    "src/sports/darts/commands.py",
    "src/sports/darts/events.py",
    "src/sports/darts/state.py",
    "src/sports/darts/ruleset.py",
    "src/sports/darts/result.py",
    "src/sports/darts/config.py",
    "src/sports/darts/entities.py",
    "src/sports/darts/plugin.py",
    "src/sports/darts/player.py",
    "src/console/football_view.py",
    "src/console/darts_view.py",
]


def patch_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = text.replace(AGGREGATE_IMPORT, AGGREGATE_REPLACEMENT)
    if text != original:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    for py in PROJECT.rglob("*.py"):
        if "tools/" in str(py).replace("\\", "/"):
            continue
        patch_file(py)

    for rel in OBSOLETE:
        p = PROJECT / rel
        if p.exists():
            p.unlink()
            print("removed", rel)

    print("Import rewrite complete.")


if __name__ == "__main__":
    main()
