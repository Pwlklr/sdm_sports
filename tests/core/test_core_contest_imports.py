from __future__ import annotations

import ast
from pathlib import Path


def test_core_contest_does_not_import_sports() -> None:
    contest_dir = Path(__file__).resolve().parents[2] / "src" / "core" / "contest"
    offenders: list[str] = []
    for path in sorted(contest_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("src.sports"):
                    offenders.append(
                        f"{path.relative_to(contest_dir.parent.parent)}: {node.module}"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("src.sports"):
                        offenders.append(
                            f"{path.relative_to(contest_dir.parent.parent)}: {alias.name}"
                        )
    assert offenders == []
