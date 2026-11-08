"""Generator for ARC task 42a28f889145: swap two object colors.

The input contains exactly two separated, uniformly colored 4-connected blobs.
The reference rule keeps both shapes and positions fixed while exchanging their
colors.  The sampler deliberately varies shape identity, palette, placement and
left/right color order; the latter defeats the canonical-only shortcut "put the
larger color on the left".
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "42a28f889145"
TASK_ID = GENERATOR_ID
RULE_HASH = "57cc84264d9e"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background grid contains exactly two separated 4-connected blobs in "
    "distinct nonzero colors. Sort the objects left-to-right and exchange their "
    "colors while preserving every occupied cell. Shapes may match or differ; "
    "both relative color orders are generated."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors",
    "exactly two uniformly colored 4-connected nonzero objects",
    "each object contains 3..6 cells",
    "the objects have disjoint column ranges with at least one blank column between them",
    "the two object colors are distinct",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted toward 7", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "weighted toward 9..10", "valid": "9..16"},
    "shape_pair": {
        "type": "int",
        "default": "difficulty-weighted ordered pair",
        "valid": "0..35",
    },
    "color_pair": {
        "type": "int",
        "default": "uniform unordered pair from colors 1..9",
        "valid": "0..35",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Six distinct, canonical-compatible connected blobs, all within a 3x3 box.
# The first five include every normalized shape present in the canonical pairs.
_SHAPES = (
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 2)),
)
_SHAPE_COUNT = len(_SHAPES)
_COLOR_PAIRS = tuple(combinations(range(1, 10), 2))
_COLOR_PAIR_INDEX = {pair: index for index, pair in enumerate(_COLOR_PAIRS)}


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


_SHAPE_INDEX = {_normalize(shape): index for index, shape in enumerate(_SHAPES)}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _weighted_int(ctx, label, lo, hi, favored=()):
    """Keep the full exact domain available while weighting ordinary draws."""
    return ctx.draw_choice(label, list(range(lo, hi + 1)) + list(favored))


def _shape_options(difficulty):
    all_pairs = list(range(_SHAPE_COUNT * _SHAPE_COUNT))
    if difficulty == "easy":
        favored = [
            index
            for index in all_pairs
            if len(_SHAPES[index // _SHAPE_COUNT]) <= 4
            and len(_SHAPES[index % _SHAPE_COUNT]) <= 4
        ]
    elif difficulty == "hard":
        favored = [
            index
            for index in all_pairs
            if len(_SHAPES[index // _SHAPE_COUNT])
            + len(_SHAPES[index % _SHAPE_COUNT])
            >= 10
        ]
    else:
        favored = all_pairs
    return all_pairs + favored + favored


def _shape_size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _paint(grid, cells, row0, col0, color):
    for dr, dc in cells:
        grid[row0 + dr][col0 + dc] = color


def _draw_layout(ctx, h, w, left, right):
    left_h, left_w = _shape_size(left)
    right_h, right_w = _shape_size(right)
    horizontal_room = w - left_w - right_w
    if horizontal_room < 1:
        raise ValueError("grid is too narrow for two separated shapes")

    # Split the remaining columns among left margin, positive gap and right margin.
    column_layouts = []
    for gap in range(1, horizontal_room + 1):
        slack = horizontal_room - gap
        for left_margin in range(slack + 1):
            left_col = left_margin
            right_col = left_col + left_w + gap
            column_layouts.append((left_col, right_col))
    left_col, right_col = ctx.draw_rng("column_layout").choice(column_layouts)
    left_row = ctx.draw_rng("left_row").randint(0, h - left_h)
    right_row = ctx.draw_rng("right_row").randint(0, h - right_h)
    return left_row, left_col, right_row, right_col


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Strong canonical-profile mass in every band, while every advertised value
    # remains directly requestable. The dimensions are independent keyed draws.
    h = _weighted_int(ctx, "grid_h", 7, 12, favored=(7,) * 30)
    w = _weighted_int(ctx, "grid_w", 9, 16, favored=(9, 10) * 15)
    shape_pair = ctx.draw_choice("shape_pair", _shape_options(difficulty))
    color_pair = ctx.draw_choice("color_pair", list(range(len(_COLOR_PAIRS))))

    left_shape = _SHAPES[shape_pair // _SHAPE_COUNT]
    right_shape = _SHAPES[shape_pair % _SHAPE_COUNT]
    low_color, high_color = _COLOR_PAIRS[color_pair]

    # Alternation is a teaching schedule, not an output rule. Every four
    # consecutive materialized pairs—and every three-demo rotation of them—show
    # both color orders, refuting the canonical-fitting descending-sort shortcut.
    if sample_index % 2:
        left_color, right_color = high_color, low_color
    else:
        left_color, right_color = low_color, high_color

    left_row, left_col, right_row, right_col = _draw_layout(
        ctx, h, w, left_shape, right_shape
    )
    grid = full_grid(h, w, 0)
    _paint(grid, left_shape, left_row, left_col, left_color)
    _paint(grid, right_shape, right_row, right_col, right_color)
    return grid


def _objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    records = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = current_row + dr, current_col + dc
                    nr, nc = neighbor
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            records.append(
                {
                    "color": color,
                    "cells": frozenset(cells),
                    "min_row": min(rows),
                    "max_row": max(rows),
                    "min_col": min(cols),
                    "max_col": max(cols),
                    "shape": _normalize(cells),
                }
            )
    return sorted(records, key=lambda record: (record["min_col"], record["min_row"]))


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    height = len(grid)
    if not 7 <= height <= 12:
        errors.append(f"grid height {height} outside 7..12")
    if not 9 <= width <= 16:
        errors.append(f"grid width {width} outside 9..16")

    records = _objects(grid)
    if len(records) != 2:
        errors.append(f"expected exactly 2 nonzero objects, found {len(records)}")
        return errors
    colors = {record["color"] for record in records}
    if len(colors) != 2:
        errors.append("the two objects must have distinct colors")
    for index, record in enumerate(records):
        size = len(record["cells"])
        if not 3 <= size <= 6:
            errors.append(f"object {index} has {size} cells, expected 3..6")
    gap = records[1]["min_col"] - records[0]["max_col"] - 1
    if gap < 1:
        errors.append(f"objects require at least one blank separating column; gap={gap}")
    return errors


def strict_canonical_like(grid):
    """Accept exactly the lawful manifold owned by this sampler."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    left, right = _objects(grid)
    try:
        left_shape = _SHAPE_INDEX[left["shape"]]
        right_shape = _SHAPE_INDEX[right["shape"]]
    except KeyError as exc:
        raise ValueError("object shape is outside the generated shape vocabulary") from exc
    color_key = tuple(sorted((left["color"], right["color"])))
    try:
        color_pair = _COLOR_PAIR_INDEX[color_key]
    except KeyError as exc:
        raise ValueError("object colors are outside the generated palette") from exc
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_pair": left_shape * _SHAPE_COUNT + right_shape,
        "color_pair": color_pair,
    }


def _swap_object_colors(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("swap rule requires a lawful input: " + "; ".join(errors))
    left, right = _objects(grid)
    output = [list(row) for row in grid]
    for row, col in left["cells"]:
        output[row][col] = right["color"]
    for row, col in right["cells"]:
        output[row][col] = left["color"]
    return output


def _sort_colors_descending(grid):
    """Plausible rival: place the larger color left and smaller color right."""
    errors = self_check(grid)
    if errors:
        raise ValueError("rival requires a lawful input: " + "; ".join(errors))
    left, right = _objects(grid)
    high, low = sorted((left["color"], right["color"]), reverse=True)
    output = [list(row) for row in grid]
    for row, col in left["cells"]:
        output[row][col] = high
    for row, col in right["cells"]:
        output[row][col] = low
    return output


def _has_left_greater_color(grid):
    try:
        left, right = _objects(grid)
    except Exception:
        return False
    return len((left, right)) == 2 and left["color"] > right["color"]


def lesson_identifiable(demos, query):
    """Require demonstrations in both color orders to refute sorting shortcuts."""
    del query  # The teaching requirement depends on demonstrations only.
    orders = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(grid)
        if errors:
            return [f"demo {index} is outside the lawful manifold: {'; '.join(errors)}"]
        if output != _swap_object_colors(grid):
            return [f"demo {index} label does not exchange the two object colors"]
        left, right = _objects(grid)
        orders.add(left["color"] > right["color"])
    if orders != {False, True}:
        return [
            "demonstrations must include both left-color<right-color and "
            "left-color>right-color cases to refute color-sorting shortcuts"
        ]
    return []


SEMANTIC_WITNESSES = {"left_color_greater": _has_left_greater_color}
SEMANTIC_RIVALS = {"sort_colors_descending": _sort_colors_descending}
WITNESS_RIVALS = {"left_color_greater": ["sort_colors_descending"]}
CANONICAL_SHORTCUTS = {"sort_colors_descending": _sort_colors_descending}
LESSON_COMPETITORS = {"sort_colors_descending": _sort_colors_descending}
