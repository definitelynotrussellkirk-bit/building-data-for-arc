"""Independent oracle and reusable review helpers for task aa378df15340.

This is test/review tooling, not label authority.  The transformation is
implemented directly from coordinates so tests do not depend on production
helpers.  Canonical Racket execution remains authoritative.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

TASK_ID = "aa378df15340"
ROOT = Path(__file__).resolve().parents[3]


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transpose_add_output(grid: list[list[int]]) -> list[list[int]]:
    """Preserve every source and copy it to its main-diagonal transpose."""
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                out[col][row] = value
    return out


def upper_triangle_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: copy only sources above the diagonal."""
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and row < col:
                out[col][row] = value
    return out


def marks(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def observed(grid: list[list[int]]) -> dict[str, int]:
    values = [value for _, _, value in marks(grid)]
    return {
        "grid_n": len(grid),
        "n_seeds": len(values),
        "n_colors": len(set(values)),
    }


def teaching_errors(grid: list[list[int]]) -> list[str]:
    errors: list[str] = []
    coords = [(row, col) for row, col, _ in marks(grid)]
    if not any(row < col for row, col in coords):
        errors.append("missing an upper-triangle source")
    if not any(row > col for row, col in coords):
        errors.append("missing a lower-triangle source")
    if any(row == col for row, col in coords):
        errors.append("diagonal source present")
    occupied = [(row, col) for row, col in coords if grid[col][row] != 0]
    if occupied:
        errors.append(f"transpose target already occupied: {occupied[:3]}")
    if transpose_add_output(grid) == upper_triangle_only(grid):
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
