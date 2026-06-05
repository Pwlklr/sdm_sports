#!/bin/bash

echo "=== Running MyPy ==="
mypy src/ --strict

echo "=== Running ruff ==="
ruff check --fix src/ tests/

echo "=== Running black ==="
black src/ tests/