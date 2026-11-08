"""Independent review probes for ARC task aeb31f908966.

The generator is loaded dynamically, but every rule oracle, rival solver,
observable-axis parser, and witness predicate in this module is implemented
independently of ``generator.py``.  Future reviewers can therefore use it to
catch semantic drift rather than merely comparing the generator to itself.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Callable

TASK_ID = "aeb31f908966"
Grid = list[list[int]]


def load_generator(path: str | None = None) -> ModuleType:
    source = Path(path).resolve() if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_grid(grid: object) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def chosen_axis(grid: Grid) -> tuple[str, int]:
    """Return the canonical orientation and axis index.

    The canonical authority chooses a top-edge marker whenever one exists;
    otherwise it uses the first left-edge marker.  Lawful task inputs contain
    exactly one marker, never at the top-left corner.
    """
    height, width = validate_grid(grid)
    top = [col for col in range(width) if grid[0][col] == 2]
    if top:
        return "top", top[0]
    left = [row for row in range(height) if grid[row][0] == 2]
    if left:
        return "left", left[0]
    raise ValueError("grid has no top- or left-edge color-2 marker")


def mirror_target(grid: Grid, row: int, col: int) -> tuple[int, int]:
    orientation, axis = chosen_axis(grid)
    if orientation == "top":
        return row, 2 * axis - col
    return 2 * axis - row, col


def _source_fives(grid: Grid) -> list[tuple[int, int]]:
    validate_grid(grid)
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]


def rule_output(grid: Grid) -> Grid:
    """Independent intended rule: add in-bounds reflections only onto zeroes."""
    height, width = validate_grid(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        mirror_row, mirror_col = mirror_target(grid, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            if output[mirror_row][mirror_col] == 0:
                output[mirror_row][mirror_col] = 7
    return output


def overwrite_occupied(grid: Grid) -> Grid:
    """Canonical-fitting rival: overwrite every in-bounds mirror target."""
    height, width = validate_grid(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        mirror_row, mirror_col = mirror_target(grid, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            output[mirror_row][mirror_col] = 7
    return output


def wrap_out_of_bounds(grid: Grid) -> Grid:
    """Canonical-fitting rival: wrap an out-of-bounds reflection modulo size."""
    height, width = validate_grid(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        mirror_row, mirror_col = mirror_target(grid, row, col)
        mirror_row %= height
        mirror_col %= width
        if output[mirror_row][mirror_col] == 0:
            output[mirror_row][mirror_col] = 7
    return output


def _one_side_only(grid: Grid, side: str) -> Grid:
    height, width = validate_grid(grid)
    orientation, axis = chosen_axis(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        coordinate = col if orientation == "top" else row
        if side == "negative" and coordinate >= axis:
            continue
        if side == "positive" and coordinate <= axis:
            continue
        mirror_row, mirror_col = mirror_target(grid, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            if output[mirror_row][mirror_col] == 0:
                output[mirror_row][mirror_col] = 7
    return output


def negative_side_only(grid: Grid) -> Grid:
    """Rival that reflects only sources left/above the selected axis."""
    return _one_side_only(grid, "negative")


def positive_side_only(grid: Grid) -> Grid:
    """Rival that reflects only sources right/below the selected axis."""
    return _one_side_only(grid, "positive")


def vertical_axis_only(grid: Grid) -> Grid:
    """Rival that implements only the top-marker/vertical-axis branch."""
    orientation, _axis = chosen_axis(grid)
    return rule_output(grid) if orientation == "top" else deepcopy(grid)


def horizontal_axis_only(grid: Grid) -> Grid:
    """Rival that implements only the left-marker/horizontal-axis branch."""
    orientation, _axis = chosen_axis(grid)
    return rule_output(grid) if orientation == "left" else deepcopy(grid)


def identity(grid: Grid) -> Grid:
    validate_grid(grid)
    return deepcopy(grid)


def observed(grid: Grid) -> dict[str, int | str]:
    height, width = validate_grid(grid)
    orientation, axis = chosen_axis(grid)
    fives = _source_fives(grid)
    negative = 0
    positive = 0
    any_oob = False
    any_occupied = False
    for row, col in fives:
        coordinate = col if orientation == "top" else row
        if coordinate < axis:
            negative += 1
        elif coordinate > axis:
            positive += 1
        mirror_row, mirror_col = mirror_target(grid, row, col)
        if not (0 <= mirror_row < height and 0 <= mirror_col < width):
            any_oob = True
        elif grid[mirror_row][mirror_col] == 5:
            any_occupied = True
    if negative == positive:
        raise ValueError("shape side is not observable: equal source counts on both sides")
    edge_case = "out_of_bounds" if any_oob else "occupied" if any_occupied else "clean"
    return {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "shape_side": "negative" if negative > positive else "positive",
        "n_5cells": len(fives),
        "edge_case": edge_case,
    }


def profile(grid: Grid) -> tuple[int, int, int]:
    height, width = validate_grid(grid)
    return height, width, len({value for row in grid for value in row})


def has_occupied_target(grid: Grid) -> bool:
    try:
        return observed(grid)["edge_case"] == "occupied"
    except ValueError:
        return False


def has_out_of_bounds_target(grid: Grid) -> bool:
    try:
        return observed(grid)["edge_case"] == "out_of_bounds"
    except ValueError:
        return False


def has_negative_side_source(grid: Grid) -> bool:
    try:
        return observed(grid)["shape_side"] == "negative"
    except ValueError:
        return False


def has_positive_side_source(grid: Grid) -> bool:
    try:
        return observed(grid)["shape_side"] == "positive"
    except ValueError:
        return False


def has_top_axis(grid: Grid) -> bool:
    try:
        return chosen_axis(grid)[0] == "top"
    except ValueError:
        return False


def has_left_axis(grid: Grid) -> bool:
    try:
        return chosen_axis(grid)[0] == "left"
    except ValueError:
        return False


def rival_disagrees(grid: Grid, rival: Callable[[Grid], Grid]) -> bool:
    return rival(grid) != rule_output(grid)
