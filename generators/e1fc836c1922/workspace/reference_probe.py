"""Independent oracle and reusable audit helpers for task e1fc836c1922.

This file is test/review tooling, not label authority.  The transformation is
implemented directly from coordinates so tests do not depend on production
helpers.  Canonical Racket execution remains the authoritative runtime check.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

TASK_ID = "e1fc836c1922"
ROOT = Path(__file__).resolve().parents[3]


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mirror_output(grid: list[list[int]]) -> list[list[int]]:
    """Copy every nonzero source cell to its main-diagonal transpose."""
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                out[col][row] = value
    return out


def upper_triangle_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: reflect only sources above the diagonal."""
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and row < col:
                out[col][row] = value
    return out


def observed(grid: list[list[int]]) -> dict[str, int]:
    marks = [value for row in grid for value in row if value != 0]
    return {
        "grid_size": len(grid),
        "n_marks": len(marks),
        "n_colors": len(set(marks)),
    }


def teaching_errors(grid: list[list[int]]) -> list[str]:
    errors: list[str] = []
    marks = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not any(row < col for row, col in marks):
        errors.append("missing an upper-triangle source")
    if not any(row > col for row, col in marks):
        errors.append("missing a lower-triangle source")
    if any(row == col for row, col in marks):
        errors.append("diagonal source present")
    if any(grid[col][row] != 0 for row, col in marks):
        errors.append("a transpose target is already occupied")
    if mirror_output(grid) == upper_triangle_only(grid):
        errors.append("upper-triangle-only shortcut is not refuted")
    return errors


def malformed_grids() -> tuple[Any, ...]:
    return (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[10, 0], [0, 0]],
    )
