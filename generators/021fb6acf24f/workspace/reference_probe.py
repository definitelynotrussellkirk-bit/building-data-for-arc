"""Independent review probes for ARC task 021fb6acf24f.

This module deliberately does not import semantic helpers from generator.py.  It
provides a portable oracle, observable parser, and two canonical-fitting rivals
for focused tests and future reviewers.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType

TASK_ID = "021fb6acf24f"


def load_generator(path: str | None = None) -> ModuleType:
    source = Path(path).resolve() if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_rectangular_grid(grid: object) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def scan_colors(grid: list[list[int]]) -> list[int]:
    """Distinct non-background colors in row-major first-occurrence order."""
    _validate_rectangular_grid(grid)
    seen: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.append(value)
    return seen


def _bbox_by_color(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"color {color} is absent")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent intended rule: ascending colors fill remaining bbox zeros."""
    _validate_rectangular_grid(grid)
    output = deepcopy(grid)
    for color in sorted(scan_colors(grid)):
        r0, c0, r1, c1 = _bbox_by_color(grid, color)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if output[row][col] == 0:
                    output[row][col] = color
    return output


def scan_color_order(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: process scan order, not ascending color order."""
    _validate_rectangular_grid(grid)
    output = deepcopy(grid)
    for color in scan_colors(grid):
        r0, c0, r1, c1 = _bbox_by_color(grid, color)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if output[row][col] == 0:
                    output[row][col] = color
    return output


def late_overwrite(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: later bboxes overwrite original background."""
    _validate_rectangular_grid(grid)
    original = deepcopy(grid)
    output = deepcopy(grid)
    for color in sorted(scan_colors(grid)):
        r0, c0, r1, c1 = _bbox_by_color(grid, color)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if original[row][col] == 0:
                    output[row][col] = color
    return output


def identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def observed(grid: list[list[int]]) -> dict[str, int]:
    height, width = _validate_rectangular_grid(grid)
    return {
        "grid_h": height,
        "grid_w": width,
        "n_colors": len(scan_colors(grid)),
    }


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    state = observed(grid)
    return state["grid_h"], state["grid_w"], state["n_colors"] + 1


def has_order_contest(grid: list[list[int]]) -> bool:
    """Whether both named canonical-fitting rivals disagree with the rule."""
    expected = rule_output(grid)
    return scan_color_order(grid) != expected and late_overwrite(grid) != expected
