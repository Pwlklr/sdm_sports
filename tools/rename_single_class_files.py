#!/usr/bin/env python3
"""Rename single-class modules to snake_case class names and rewrite imports."""
from __future__ import annotations

import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"


def to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def class_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(r"^class (\w+)", text, re.M)
    if len(matches) != 1:
        return None
    return matches[0]


def build_renames() -> dict[str, str]:
    renames: dict[str, str] = {}
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        cls = class_name(path)
        if cls is None:
            continue
        expected = f"{to_snake(cls)}.py"
        if path.name != expected:
            renames[path.as_posix()] = path.with_name(expected).as_posix()
    return renames


def module_path(file_path: str) -> str:
    """src/core/contest/aggregate.py -> src.core.contest.aggregate"""
    rel = Path(file_path).relative_to(PROJECT)
    return ".".join(rel.with_suffix("").parts)


def main() -> None:
    renames = build_renames()
    if not renames:
        print("No renames needed.")
        return

    import_map: list[tuple[str, str]] = []
    for old, new in sorted(renames.items()):
        old_mod = module_path(old)
        new_mod = module_path(new)
        import_map.append((old_mod, new_mod))
        print(f"{Path(old).relative_to(PROJECT)} -> {Path(new).relative_to(PROJECT)}")

    for py in PROJECT.rglob("*.py"):
        if "tools/" in py.as_posix():
            continue
        text = py.read_text(encoding="utf-8")
        original = text
        for old_mod, new_mod in import_map:
            text = text.replace(old_mod, new_mod)
        if text != original:
            py.write_text(text, encoding="utf-8")

    for old, new in renames.items():
        old_path = PROJECT / Path(old).relative_to(PROJECT)
        new_path = PROJECT / Path(new).relative_to(PROJECT)
        if old_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)

    print(f"Renamed {len(renames)} files.")


if __name__ == "__main__":
    main()
