#!/usr/bin/env python3
"""One-off: copy sources into aggregate-oriented package layout."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"

DIRS = [
    "core/contest",
    "core/contestant",
    "core/tournament",
    "core/sport",
    "core/system",
    "core/shared",
    "sports/football/contest",
    "sports/football/contestant",
    "sports/football/console",
    "sports/darts/contest",
    "sports/darts/contestant",
    "sports/darts/console",
]
for rel in DIRS:
    (ROOT / rel).mkdir(parents=True, exist_ok=True)

CORE_MOVES = {
    "core/command.py": "core/contest/command.py",
    "core/contest_event.py": "core/contest/event.py",
    "core/contest_state.py": "core/contest/state.py",
    "core/contest.py": "core/contest/aggregate.py",
    "core/result.py": "core/contest/result.py",
    "core/ruleset.py": "core/contest/ruleset.py",
    "core/observer.py": "core/contest/observer.py",
    "core/contestant.py": "core/contestant/models.py",
    "core/tournament.py": "core/tournament/aggregate.py",
    "core/tournament_event.py": "core/tournament/event.py",
    "core/tournament_state.py": "core/tournament/state.py",
    "core/tournament_phase.py": "core/tournament/phase.py",
    "core/tournament_policy.py": "core/tournament/policy.py",
    "core/draw_strategies.py": "core/tournament/draw.py",
    "core/sport_factory.py": "core/sport/factory.py",
    "core/console_adapter.py": "core/sport/adapter.py",
    "core/engine.py": "core/system/engine.py",
    "core/exceptions.py": "core/shared/exceptions.py",
    "core/domain_event.py": "core/shared/domain_event.py",
}

FOOTBALL_MOVES = {
    "sports/football/commands.py": "sports/football/contest/commands.py",
    "sports/football/events.py": "sports/football/contest/events.py",
    "sports/football/state.py": "sports/football/contest/state.py",
    "sports/football/ruleset.py": "sports/football/contest/ruleset.py",
    "sports/football/result.py": "sports/football/contest/result.py",
    "sports/football/config.py": "sports/football/contest/config.py",
    "sports/football/entities.py": "sports/football/contest/entities.py",
    "sports/football/plugin.py": "sports/football/adapter.py",
    "sports/football/player.py": "sports/football/contestant/player.py",
}

DARTS_MOVES = {
    "sports/darts/commands.py": "sports/darts/contest/commands.py",
    "sports/darts/events.py": "sports/darts/contest/events.py",
    "sports/darts/state.py": "sports/darts/contest/state.py",
    "sports/darts/ruleset.py": "sports/darts/contest/ruleset.py",
    "sports/darts/result.py": "sports/darts/contest/result.py",
    "sports/darts/config.py": "sports/darts/contest/config.py",
    "sports/darts/entities.py": "sports/darts/contest/entities.py",
    "sports/darts/plugin.py": "sports/darts/adapter.py",
    "sports/darts/player.py": "sports/darts/contestant/player.py",
}

CONSOLE_MOVES = {
    "console/football_view.py": "sports/football/console/view.py",
    "console/darts_view.py": "sports/darts/console/view.py",
}


def copy_map(mapping: dict[str, str]) -> None:
    for src, dst in mapping.items():
        source = ROOT / src
        target = ROOT / dst
        if source.exists():
            shutil.copy2(source, target)


def main() -> None:
    copy_map(CORE_MOVES)
    copy_map(FOOTBALL_MOVES)
    copy_map(DARTS_MOVES)
    copy_map(CONSOLE_MOVES)
    if (ROOT / "sports/football/factory.py").exists():
        pass  # stays in place
    if (ROOT / "sports/darts/factory.py").exists():
        pass
    print("Copy complete.")


if __name__ == "__main__":
    main()
