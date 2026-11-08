"""Semantic generator for ARC task 80bd3177b03c.

The executable rule connects a color only when it occurs exactly twice, the two
markers are row- or column-aligned, and every interior cell on that segment is
zero.  Standard generated lessons use distinct colors and nonintersecting clear
segments.  Their first three sample indices deliberately teach horizontal,
vertical, and mixed orientation families in that order.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "80bd3177b03c"
TASK_ID = "80bd3177b03c"
VERSION = "2.2.0"
SUMMARY = (
    "Generate two-marker colors on clear, nonintersecting horizontal and/or "
    "vertical segments.  The first three default examples cover horizontal, "
    "vertical, and mixed orientations; the exact rule connects only colors "
    "occurring twice on a clear aligned path."
)
EXAMPLES_NEEDED = 3

POSITION_BIASES = (
    "horizontal_row_pairs",
    "vertical_column_pairs",
    "mixed_pairs",
)
DEGENERATE_TEXTURES = ("no_pairs", "pairs_adjacent", "multiple_pairs_same_row")
HELPFUL_TEXTURES = ()

INVARIANTS = [
    "background is 0",
    "each standard active color appears exactly twice",
    "paired markers are row- or column-aligned with at least one zero between",
    "horizontal pairs use distinct rows and vertical pairs use distinct columns",
    "the complete output segments of different colors do not intersect",
    "the first three default sample indices cover horizontal, vertical, and mixed pairs",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w": {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "n_pairs": {"type": "int", "default": "rng 2..5", "valid": "2..8"},
    "position_bias": {
        "type": "str",
        "default": "sample-index schedule: horizontal|vertical|mixed",
        "valid": "|".join(POSITION_BIASES),
    },
    "texture": {
        "type": "str",
        "default": "standard",
        "valid": "standard|" + "|".join(DEGENERATE_TEXTURES),
    },
}


def _strict_int_draw(ctx, label, default_low, default_high, valid_low, valid_high):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_low, valid_high)
    return ctx.draw_int_strict(label, default_low, default_high)


def _position_bias(ctx, sample_index):
    if "position_bias" in ctx.overrides and ctx.overrides["position_bias"] is not None:
        return ctx.draw_choice("position_bias", POSITION_BIASES)
    scheduled = POSITION_BIASES[sample_index % len(POSITION_BIASES)]
    return ctx.draw_choice("position_bias", (scheduled,))


def _orientations(position_bias, n_pairs):
    if position_bias == "horizontal_row_pairs":
        return ["h"] * n_pairs
    if position_bias == "vertical_column_pairs":
        return ["v"] * n_pairs
    if position_bias == "mixed_pairs":
        if n_pairs < 2:
            raise ValueError("mixed_pairs requires at least two pairs")
        return ["h" if index % 2 == 0 else "v" for index in range(n_pairs)]
    raise ValueError(f"unknown position_bias: {position_bias!r}")


def _candidate_segments(height, width, orientation):
    if orientation == "h":
        return [
            {
                "orientation": "h",
                "line": row,
                "cells": tuple((row, col) for col in range(left, right + 1)),
                "endpoints": ((row, left), (row, right)),
            }
            for row in range(height)
            for left in range(width - 2)
            for right in range(left + 2, width)
        ]
    return [
        {
            "orientation": "v",
            "line": col,
            "cells": tuple((row, col) for row in range(top, bottom + 1)),
            "endpoints": ((top, col), (bottom, col)),
        }
        for col in range(width)
        for top in range(height - 2)
        for bottom in range(top + 2, height)
    ]


def _place_segments(height, width, orientations, rng):
    horizontal_needed = orientations.count("h")
    vertical_needed = orientations.count("v")
    if horizontal_needed > height:
        raise ValueError(f"{horizontal_needed} horizontal pairs do not fit in {height} rows")
    if vertical_needed > width:
        raise ValueError(f"{vertical_needed} vertical pairs do not fit in {width} columns")

    candidates = {orientation: _candidate_segments(height, width, orientation) for orientation in ("h", "v")}
    for options in candidates.values():
        rng.shuffle(options)

    # Place the scarcer orientation first in mixed scenes.  This is only a
    # search-order decision; returned segments retain no semantic ordering.
    ordered = sorted(
        orientations,
        key=lambda orientation: len(candidates[orientation]),
    )
    attempts = 0
    limit = 250_000

    def search(index, occupied, used_rows, used_cols, chosen):
        nonlocal attempts
        if index == len(ordered):
            return list(chosen)
        orientation = ordered[index]
        for candidate in candidates[orientation]:
            attempts += 1
            if attempts > limit:
                return None
            line = candidate["line"]
            if orientation == "h" and line in used_rows:
                continue
            if orientation == "v" and line in used_cols:
                continue
            cells = set(candidate["cells"])
            if cells & occupied:
                continue
            chosen.append(candidate)
            result = search(
                index + 1,
                occupied | cells,
                used_rows | ({line} if orientation == "h" else set()),
                used_cols | ({line} if orientation == "v" else set()),
                chosen,
            )
            if result is not None:
                return result
            chosen.pop()
        return None

    result = search(0, set(), set(), set(), [])
    if result is None:
        raise ValueError(
            f"could not place {len(orientations)} nonintersecting {orientations!r} pairs "
            f"on a {height}x{width} grid"
        )
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    texture = overrides.get("texture", "standard")
    if texture not in ("standard", *DEGENERATE_TEXTURES):
        raise ValueError(f"unknown texture: {texture!r}")
    if texture in DEGENERATE_TEXTURES:
        extra = set(overrides) - {"texture"}
        if extra:
            raise ValueError(f"degenerate texture cannot be combined with controls: {sorted(extra)!r}")
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        height = _strict_int_draw(ctx, "grid_h", 8, 9, 4, 20)
        width = _strict_int_draw(ctx, "grid_w", 8, 9, 4, 20)
        n_pairs = _strict_int_draw(ctx, "n_pairs", 2, 2, 2, 8)
    elif difficulty == "hard":
        height = _strict_int_draw(ctx, "grid_h", 11, 13, 4, 20)
        width = _strict_int_draw(ctx, "grid_w", 11, 13, 4, 20)
        n_pairs = _strict_int_draw(ctx, "n_pairs", 3, 5, 2, 8)
    else:
        height = _strict_int_draw(ctx, "grid_h", 8, 13, 4, 20)
        width = _strict_int_draw(ctx, "grid_w", 8, 13, 4, 20)
        n_pairs = _strict_int_draw(ctx, "n_pairs", 2, 5, 2, 8)
    position_bias = _position_bias(ctx, sample_index)
    orientations = _orientations(position_bias, n_pairs)
    rng = ctx.draw_rng("placement")
    segments = _place_segments(height, width, orientations, rng)
    colors = rng.sample(range(1, 10), n_pairs)

    grid = full_grid(height, width, 0)
    for color, segment in zip(colors, segments):
        for row, col in segment["endpoints"]:
            grid[row][col] = color
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid marker-pair lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"position_bias": position_bias, "n_pairs": n_pairs}:
        raise AssertionError(f"generated controls were not observable: wanted {position_bias!r}, got {observed!r}")
    return grid


def _draw_from_degenerate(name):
    grid = full_grid(9, 9, 0)
    if name == "no_pairs":
        grid[2][3] = 4
        grid[5][7] = 6
    elif name == "pairs_adjacent":
        grid[2][3] = grid[2][4] = 4
        grid[5][6] = grid[5][7] = 6
    elif name == "multiple_pairs_same_row":
        grid[3][1] = grid[3][3] = 4
        grid[3][5] = grid[3][7] = 6
    else:
        raise ValueError(f"unknown degenerate texture: {name!r}")
    return grid


def _points_by_color(grid):
    points = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                points[value].append((row, col))
    return dict(points)


def _segment(points):
    (row1, col1), (row2, col2) = sorted(points)
    if row1 == row2:
        return [(row1, col) for col in range(min(col1, col2), max(col1, col2) + 1)]
    if col1 == col2:
        return [(row, col1) for row in range(min(row1, row2), max(row1, row2) + 1)]
    return []


def rule_mirror(grid):
    """Exact Python mirror of the broad canonical Racket rule."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    records = []
    for color, points in _points_by_color(grid).items():
        if len(points) == 2:
            ordered = tuple(sorted(points))
            records.append((ordered[0], color, ordered))
    records.sort(key=lambda record: record[0])
    for _, color, points in records:
        cells = _segment(points)
        if not cells:
            continue
        endpoints = set(points)
        if all((row, col) in endpoints or grid[row][col] == 0 for row, col in cells):
            for row, col in cells:
                output[row][col] = color
    return output


def observe_overrides(grid):
    """Recover the standard lesson's orientation family and pair count."""
    if self_check(grid):
        raise ValueError("grid is not a valid standard marker-pair lesson")
    horizontal = vertical = 0
    for points in _points_by_color(grid).values():
        (row1, col1), (row2, col2) = points
        if row1 == row2:
            horizontal += 1
        elif col1 == col2:
            vertical += 1
    if horizontal and vertical:
        bias = "mixed_pairs"
    elif horizontal:
        bias = "horizontal_row_pairs"
    else:
        bias = "vertical_column_pairs"
    return {"position_bias": bias, "n_pairs": horizontal + vertical}


def _basic_grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty and rectangular"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be non-empty and rectangular"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be literal ARC color integers from zero through nine"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    by_color = _points_by_color(grid)
    if len(by_color) < 2:
        errors.append(f"expected at least two active endpoint colors, got {len(by_color)}")
    used_rows: set[int] = set()
    used_cols: set[int] = set()
    occupied_segments: set[tuple[int, int]] = set()
    for color, points in by_color.items():
        if len(points) != 2:
            errors.append(f"color {color} should appear exactly twice, got {len(points)}")
            continue
        (row1, col1), (row2, col2) = sorted(points)
        if row1 != row2 and col1 != col2:
            errors.append(f"color {color} endpoints must be row/column aligned")
            continue
        cells = _segment(points)
        if row1 == row2:
            if row1 in used_rows:
                errors.append("active row reused by more than one pair")
            used_rows.add(row1)
            if abs(col2 - col1) < 2:
                errors.append(f"color {color} horizontal pair needs a visible gap")
        else:
            if col1 in used_cols:
                errors.append("active column reused by more than one pair")
            used_cols.add(col1)
            if abs(row2 - row1) < 2:
                errors.append(f"color {color} vertical pair needs a visible gap")
        endpoints = set(points)
        if any((row, col) not in endpoints and grid[row][col] != 0 for row, col in cells):
            errors.append(f"color {color} path is not clear")
        overlap = occupied_segments.intersection(cells)
        if overlap:
            errors.append(f"color {color} output segment intersects another pair")
        occupied_segments.update(cells)
    return errors
