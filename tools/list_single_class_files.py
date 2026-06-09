#!/usr/bin/env python3
import re
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "src"
for path in sorted(src.rglob("*.py")):
    if path.name == "__init__.py":
        continue
    text = path.read_text(encoding="utf-8")
    classes = re.findall(r"^class (\w+)", text, re.M)
    if len(classes) == 1:
        print(f"{path.relative_to(src.parent)}|{classes[0]}")
