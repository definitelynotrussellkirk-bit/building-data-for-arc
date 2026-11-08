"""Generator for c6a422753abe: reflect across one blue separator line.

A lawful input has exactly one full color-1 row or column, never both. A
connected two-color source shape lies entirely on one side and fits when
reflected across the separator. The canonical output swaps the two colors at
the original source and paints an unswapped reflected copy on the empty side.
"""
from __future__ import annotations

from collections.abc import Callable
from math import ceil
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c6a422753abe"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1781c378782f"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "A zero-background grid contains exactly one full blue row or column and "
    "a connected shape using exactly two non-background colors on one side. "
    "Reflect the shape across the blue separator into the empty side. At the "
    "original location swap the shape's two colors; the reflected copy keeps "
    "the original colors and the separator remains blue."
)

SEPARATOR_AXES = ("row", "col")
SOURCE_SIDES = ("before", "after")
PALETTE_PAIRS = ("2,3", "4,8", "5,6", "2,8", "3,7", "4,9")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

INVARIANTS = [
    "exactly one full color-1 row xor one full color-1 column",
    "all non-{0,1} cells lie on one side of the separator",
    "the source uses exactly two colors and its reflection is in bounds",
    "the opposite side is empty in the input",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "8..30"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "8..30"},
    "separator_axis": {"type": "str", "default": "scheduled", "valid": "row|col"},
    "separator_index": {
        "type": "int",
        "default": "interior scheduled",
        "valid": "2..dimension-3",
        "probe": "diagnostic",
    },
    "source_side": {"type": "str", "default": "scheduled", "valid": "before|after"},
    "n_cells": {"type": "int", "default": "difficulty schedule", "valid": "4..24"},
    "palette_pair": {
        "type": "str",
        "default": "scheduled",
        "valid": "2,3|4,8|5,6|2,8|3,7|4,9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _choice(name: str, value: Any, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")
    return value


def _palette(value: Any) -> tuple[int, int]:
    if type(value) is not str:
        raise ValueError("palette_pair must be a string a,b")
    parts = value.split(",")
    if len(parts) != 2:
        raise ValueError("palette_pair must contain exactly two colors")
    try:
        colors = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ValueError("palette_pair colors must be integers") from exc
    if any(str(color) != part for color, part in zip(colors, parts)):
        raise ValueError("palette_pair must use canonical decimal integers")
    if len(set(colors)) != 2 or any(color in (0, 1) or not 0 <= color <= 9 for color in colors):
        raise ValueError("palette_pair needs two distinct colors from 2..9")
    return colors


def _dimension(ctx, overrides, name, band):
    if name in overrides:
        return _exact_int(name, overrides[name], 8, 30)
    return ctx.draw_rng(name).randint(*band)


def _legal_interval(length: int, separator: int, side: str) -> tuple[int, int]:
    if side == "before":
        return max(0, 2 * separator - (length - 1)), separator - 1
    return separator + 1, min(length - 1, 2 * separator)


def _shape_path(
    *, height: int, width: int, axis: str, separator: int, side: str, n_cells: int, rng
) -> list[tuple[int, int]]:
    """Construct a connected serpentine path with broad normal-axis coverage."""
    if axis == "col":
        lo, hi = _legal_interval(width, separator, side)
        normal = list(range(lo, hi + 1))
        if side == "after":
            normal.reverse()
        if rng.randrange(2):
            normal.reverse()
        rows_needed = ceil(n_cells / len(normal))
        if rows_needed > height:
            raise ValueError("n_cells exceeds the legal reflected region")
        start = rng.randint(0, height - rows_needed)
        path = []
        for offset, row in enumerate(range(start, start + rows_needed)):
            cols = normal if offset % 2 == 0 else list(reversed(normal))
            path.extend((row, col) for col in cols)
    else:
        lo, hi = _legal_interval(height, separator, side)
        normal = list(range(lo, hi + 1))
        if side == "after":
            normal.reverse()
        if rng.randrange(2):
            normal.reverse()
        cols_needed = ceil(n_cells / len(normal))
        if cols_needed > width:
            raise ValueError("n_cells exceeds the legal reflected region")
        start = rng.randint(0, width - cols_needed)
        path = []
        for offset, col in enumerate(range(start, start + cols_needed)):
            rows = normal if offset % 2 == 0 else list(reversed(normal))
            path.extend((row, col) for row in rows)
    return path[:n_cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    bands = {
        None: ((10, 20), (10, 22), (6, 13)),
        "easy": ((8, 12), (8, 13), (4, 7)),
        "medium": ((13, 22), (13, 24), (7, 14)),
        "hard": ((22, 30), (22, 30), (12, 24)),
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _dimension(ctx, overrides, "grid_h", bands[difficulty][0])
    width = _dimension(ctx, overrides, "grid_w", bands[difficulty][1])
    axis = _choice(
        "separator_axis",
        overrides.get("separator_axis", SEPARATOR_AXES[sample_index % 2]),
        SEPARATOR_AXES,
    )
    side = _choice(
        "source_side",
        overrides.get("source_side", SOURCE_SIDES[(sample_index // 2) % 2]),
        SOURCE_SIDES,
    )
    dimension = height if axis == "row" else width
    if "separator_index" in overrides:
        separator = _exact_int("separator_index", overrides["separator_index"], 2, dimension - 3)
    else:
        center = dimension // 2
        jitter = ctx.draw_rng("separator").choice((-2, -1, 0, 1, 2))
        separator = max(2, min(dimension - 3, center + jitter))
    palette_text = overrides.get("palette_pair", PALETTE_PAIRS[sample_index % len(PALETTE_PAIRS)])
    colors = _palette(palette_text)
    rng = ctx.draw_rng("shape")
    lo, hi = _legal_interval(dimension, separator, side)
    normal_len = hi - lo + 1
    capacity = normal_len * (width if axis == "row" else height)
    if capacity < 4:
        raise ValueError("separator leaves too little reflected source space")
    if "n_cells" in overrides:
        n_cells = _exact_int("n_cells", overrides["n_cells"], 4, 24)
    else:
        n_cells = rng.randint(*bands[difficulty][2])
    if n_cells > capacity:
        raise ValueError(f"n_cells={n_cells} exceeds legal capacity {capacity}")
    cells = _shape_path(
        height=height,
        width=width,
        axis=axis,
        separator=separator,
        side=side,
        n_cells=n_cells,
        rng=rng,
    )
    grid = full_grid(height, width, 0)
    if axis == "row":
        grid[separator] = [1] * width
    else:
        for row in range(height):
            grid[row][separator] = 1
    offset = rng.randrange(2)
    for index, (row, col) in enumerate(cells):
        # A 2/3 cadence avoids a pure checkerboard while guaranteeing both colors.
        grid[row][col] = colors[(index + index // 3 + offset) % 2]
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def _analyze_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    full_rows = [row for row in range(height) if all(grid[row][col] == 1 for col in range(width))]
    full_cols = [col for col in range(width) if all(grid[row][col] == 1 for row in range(height))]
    if (len(full_rows), len(full_cols)) not in ((1, 0), (0, 1)):
        raise ValueError("expected exactly one full color-1 row xor column")
    axis = "row" if full_rows else "col"
    separator = full_rows[0] if full_rows else full_cols[0]
    expected_ones = {(separator, col) for col in range(width)} if axis == "row" else {
        (row, separator) for row in range(height)
    }
    actual_ones = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 1}
    if actual_ones != expected_ones:
        raise ValueError("all color-1 cells must belong to the sole separator")
    source_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1)
    ]
    if not source_cells:
        raise ValueError("source shape is missing")
    colors = []
    for row, col in source_cells:
        value = grid[row][col]
        if value not in colors:
            colors.append(value)
    if len(colors) != 2:
        raise ValueError("source shape must use exactly two colors")
    coordinates = [row if axis == "row" else col for row, col in source_cells]
    if all(value < separator for value in coordinates):
        side = "before"
    elif all(value > separator for value in coordinates):
        side = "after"
    else:
        raise ValueError("source shape must lie entirely on one separator side")
    scene = {
        "height": height,
        "width": width,
        "axis": axis,
        "separator": separator,
        "side": side,
        "colors": tuple(colors),
        "source_cells": tuple(source_cells),
    }
    reflected = [_reflect(scene, row, col) for row, col in source_cells]
    if any(not 0 <= row < height or not 0 <= col < width for row, col in reflected):
        raise ValueError("source reflection leaves the grid")
    if any((row if axis == "row" else col) == separator for row, col in reflected):
        raise ValueError("source reflection lands on the separator")
    return scene


def _reflect(scene, row, col):
    if scene["axis"] == "row":
        return 2 * scene["separator"] - row, col
    return row, 2 * scene["separator"] - col


def rule_mirror(grid, *, swap_location="source"):
    if swap_location not in ("source", "reflection"):
        raise ValueError("swap_location must be source or reflection")
    scene = _analyze_grid(grid)
    output = full_grid(scene["height"], scene["width"], 0)
    if scene["axis"] == "row":
        output[scene["separator"]] = [1] * scene["width"]
    else:
        for row in range(scene["height"]):
            output[row][scene["separator"]] = 1
    first, second = scene["colors"]
    swap = {first: second, second: first}
    for row, col in scene["source_cells"]:
        value = grid[row][col]
        rr, rc = _reflect(scene, row, col)
        if swap_location == "source":
            output[row][col] = swap[value]
            output[rr][rc] = value
        else:
            output[row][col] = value
            output[rr][rc] = swap[value]
    return output


def observe_overrides(grid):
    scene = _analyze_grid(grid)
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "separator_axis": scene["axis"],
        "separator_index": scene["separator"],
        "source_side": scene["side"],
        "n_cells": len(scene["source_cells"]),
        "palette_pair": ",".join(map(str, sorted(scene["colors"]))),
    }


def _rival_copy_without_swap(grid):
    scene = _analyze_grid(grid)
    output = full_grid(scene["height"], scene["width"], 0)
    if scene["axis"] == "row":
        output[scene["separator"]] = [1] * scene["width"]
    else:
        for row in range(scene["height"]):
            output[row][scene["separator"]] = 1
    for row, col in scene["source_cells"]:
        value = grid[row][col]
        output[row][col] = value
        rr, rc = _reflect(scene, row, col)
        output[rr][rc] = value
    return output


def _rival_swap_both(grid):
    scene = _analyze_grid(grid)
    output = rule_mirror(grid)
    first, second = scene["colors"]
    swap = {first: second, second: first}
    for row, col in scene["source_cells"]:
        rr, rc = _reflect(scene, row, col)
        output[rr][rc] = swap[grid[row][col]]
    return output


def _rival_erase_source(grid):
    scene = _analyze_grid(grid)
    output = rule_mirror(grid)
    for row, col in scene["source_cells"]:
        output[row][col] = 0
    return output


LESSON_COMPETITORS: dict[str, Callable] = {
    "copy_without_swap": _rival_copy_without_swap,
    "swap_at_reflection": lambda grid: rule_mirror(grid, swap_location="reflection"),
    "swap_both": _rival_swap_both,
    "erase_source": _rival_erase_source,
}


def lesson_identifiable(demos, query):
    reasons = []
    for index, pair in enumerate(demos):
        try:
            if rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"demo {index} disagrees with the canonical rule")
        except Exception as exc:
            reasons.append(f"demo {index} is invalid: {exc}")
    try:
        query_input, query_output = query["input"], query["output"]
    except Exception as exc:
        return reasons + [f"query is malformed: {exc}"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query_input) != query_output:
            reasons.append(f"competing rule {name!r} fits demonstrations but changes the query")
    return reasons


def self_check(grid, *, difficulty=None, meta=None):
    del meta
    if difficulty not in _VALID_DIFFICULTIES:
        return [f"invalid difficulty {difficulty!r}"]
    try:
        scene = _analyze_grid(grid)
    except Exception as exc:
        return [str(exc)]
    errors = []
    if not 8 <= scene["height"] <= 30 or not 8 <= scene["width"] <= 30:
        errors.append("grid dimensions must be within 8..30")
    if not 4 <= len(scene["source_cells"]) <= 24:
        errors.append("source shape must contain 4..24 cells")
    return errors
