"""Deterministic native episode family for the color-order parameter.

Inputs contain two colored anchor pairs.  Each pair defines a large bounding
box; the boxes overlap, so whichever numeric color is processed first owns the
still-zero overlap.  Input construction is independent of the hidden setting.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

COLOR_ORDERS = ("ascending", "descending")
MAX_DEMOS = 6
MAX_QUERIES = 4
QUERY_OFFSET = MAX_DEMOS

# Ten distinct shapes cover the largest supported 6+4 request.  The first query
# is a substantive 30x30 case for every supported demonstration count.
PROFILES: tuple[tuple[int, int], ...] = (
    (7, 8),
    (9, 10),
    (10, 11),
    (12, 16),
    (20, 24),
    (24, 20),
    (30, 30),
    (6, 11),
    (15, 30),
    (30, 15),
)

_MASK64 = (1 << 64) - 1


def _mix64(value: int) -> int:
    """Stable SplitMix64 step, independent of Python hash/random state."""
    value = (value + 0x9E3779B97F4A7C15) & _MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & _MASK64
    return value ^ (value >> 31)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer; bool is forbidden")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_index(index: Any) -> int:
    if type(index) is not int:
        raise TypeError("index must be an integer; bool is forbidden")
    if not 0 <= index < len(PROFILES):
        raise ValueError(f"index must be in 0..{len(PROFILES) - 1}")
    return index


def _validate_color_order(color_order: Any) -> str:
    if type(color_order) is not str or color_order not in COLOR_ORDERS:
        raise ValueError("color_order must be exactly 'ascending' or 'descending'")
    return color_order


def _color_pair(seed: int, index: int) -> tuple[int, int]:
    state = _mix64(seed ^ ((index + 1) * 0xD1B54A32D192ED03))
    first = 1 + state % 9
    second = 1 + _mix64(state) % 8
    if second >= first:
        second += 1
    return tuple(sorted((first, second)))


def _bounds(height: int, width: int, variant: int) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Return one boundary-touching box and one overlapping shifted box."""
    choices = (
        ((0, 0, height - 2, width - 2), (1, 1, height - 1, width - 3)),
        ((0, 0, height - 1, width - 2), (1, 2, height - 2, width - 1)),
        ((0, 0, height - 2, width - 1), (2, 1, height - 1, width - 2)),
        ((0, 0, height - 1, width - 1), (1, 1, height - 2, width - 2)),
    )
    return choices[variant]


def _anchors(bounds: tuple[int, int, int, int], *, crossed: bool) -> tuple[tuple[int, int], tuple[int, int]]:
    r1, c1, r2, c2 = bounds
    if crossed:
        return (r1, c2), (r2, c1)
    return (r1, c1), (r2, c2)


def build_input(seed: int, index: int) -> list[list[int]]:
    """Build one legal two-color overlap contest independent of the setting."""
    seed = _validate_seed(seed)
    index = _validate_index(index)
    height, width = PROFILES[index]
    state = _mix64(seed + (index + 1) * 0xA24BAED4963EE407)
    low, high = _color_pair(seed, index)
    early_bounds, late_bounds = _bounds(height, width, (index + state) % 4)

    # The first two demonstrations deliberately disagree about whether the
    # numerically larger or smaller color is encountered first in row-major
    # order.  This prevents a scan-order explanation from fitting both.
    early_color, late_color = (high, low) if index % 2 == 0 else (low, high)
    early_anchors = _anchors(early_bounds, crossed=False)  # includes (0, 0)
    late_anchors = _anchors(late_bounds, crossed=bool(state & 1))

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in early_anchors:
        grid[row][col] = early_color
    for row, col in late_anchors:
        if grid[row][col] != 0:
            raise AssertionError("anchor construction collided")
        grid[row][col] = late_color
    return grid


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(grid)


def apply_rule(grid: Any, color_order: str) -> list[list[int]]:
    """Python claim for the exact Racket bbox-fill semantics."""
    source = _validate_grid(grid)
    color_order = _validate_color_order(color_order)
    colors = sorted({cell for row in source for cell in row if cell != 0})
    if color_order == "descending":
        colors.reverse()

    result = deepcopy(source)
    for color in colors:
        cells = [
            (row_index, col_index)
            for row_index, row in enumerate(source)
            for col_index, value in enumerate(row)
            if value == color
        ]
        if not cells:
            continue
        r1 = min(row for row, _ in cells)
        c1 = min(col for _, col in cells)
        r2 = max(row for row, _ in cells)
        c2 = max(col for _, col in cells)
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if result[row][col] == 0:
                    result[row][col] = color
    return result


def generate_episode(
    seed: int,
    color_order: str,
    demos: int,
    queries: int,
    program_solution: str,
) -> dict[str, Any]:
    """Return the worker-facing train/test/program payload."""
    seed = _validate_seed(seed)
    color_order = _validate_color_order(color_order)
    if type(demos) is not int or not 2 <= demos <= MAX_DEMOS:
        raise ValueError("demos must be an integer in 2..6; bool is forbidden")
    if type(queries) is not int or not 1 <= queries <= MAX_QUERIES:
        raise ValueError("queries must be an integer in 1..4; bool is forbidden")
    if type(program_solution) is not str or not program_solution.strip():
        raise ValueError("program_solution must be nonempty Racket source")

    def pair(index: int) -> dict[str, list[list[int]]]:
        input_grid = build_input(seed, index)
        return {"input": input_grid, "output": apply_rule(input_grid, color_order)}

    return {
        "train": [pair(index) for index in range(demos)],
        "test": [pair(QUERY_OFFSET + index) for index in range(queries)],
        "program_solution": program_solution,
    }
