"""Generator for 82bce7d23c06 — project a colored row into diagonals."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "82bce7d23c06"
VERSION = "2.1.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A one-row strip of width 2..10 with an exact requested number of nonzero "
    "cells, constrained by nz*width<=30. The reference expands it to an "
    "(nz*width)-square of parallel color-preserving diagonals."
)

INVARIANTS = [
    "input height is exactly 1 and background is 0",
    "1 <= nz <= width and nz*width <= 30",
    "layout and position bias never change the requested nz count",
]

NZ_LAYOUTS = ("random", "clustered", "spread", "edges", "regular_spaced")
NZ_BIASES = ("left", "right", "center", "spread")
NZ_COLOR_DISTS = ("all_distinct", "two_colors", "single_color")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_w": {"type": "int", "default": "rng 2..10", "valid": "2..10"},
    "nz_count": {
        "type": "int",
        "default": "rng 1..min(width,7,floor(30/width))",
        "valid": "1..min(width,7,floor(30/width))",
    },
    "nz_layout": {"type": "str", "default": "rng", "valid": "|".join(NZ_LAYOUTS)},
    "nz_color_dist": {
        "type": "str", "default": "rng", "valid": "|".join(NZ_COLOR_DISTS)
    },
    "nz_position_bias": {
        "type": "str", "default": "rng", "valid": "|".join(NZ_BIASES)
    },
}


def _edge_order(width, start_right=False):
    result = []
    left, right = 0, width - 1
    take_right = start_right
    while left <= right:
        if take_right:
            result.append(right)
            right -= 1
        else:
            result.append(left)
            left += 1
        take_right = not take_right
    return result


def _bias_order(bias, width):
    columns = list(range(width))
    if bias == "left":
        return columns
    if bias == "right":
        return list(reversed(columns))
    if bias == "center":
        center = (width - 1) / 2
        return sorted(columns, key=lambda col: (abs(col - center), col))
    return _edge_order(width)


def _evenly_spaced(width, count):
    if count == 1:
        return [width // 2]
    chosen = []
    for index in range(count):
        candidate = round(index * (width - 1) / (count - 1))
        if candidate not in chosen:
            chosen.append(candidate)
    # Rounding can only reduce the count for tiny widths; fill deterministically.
    chosen.extend(col for col in range(width) if col not in chosen)
    return chosen[:count]


def _layout_positions(layout, bias, width, count, rng):
    """Return exactly ``count`` distinct columns; bias is a preference only."""
    if not (1 <= count <= width):
        raise ValueError(f"count {count} outside 1..{width}")
    bias_order = _bias_order(bias, width)
    if layout == "random":
        preferred = bias_order[: max(count, (width + 1) // 2)]
        remainder = [col for col in bias_order if col not in preferred]
        rng.shuffle(preferred)
        rng.shuffle(remainder)
        positions = preferred + remainder
    elif layout == "clustered":
        anchor = bias_order[0]
        positions = sorted(range(width), key=lambda col: (abs(col - anchor), bias_order.index(col)))
    elif layout == "spread":
        base = _evenly_spaced(width, count)
        positions = base + [col for col in bias_order if col not in base]
    elif layout == "edges":
        start_right = bias == "right"
        base = _edge_order(width, start_right=start_right)
        if bias == "center":
            center_order = _bias_order("center", width)
            # Keep true edges first, then prefer central fill columns.
            edge_prefix = base[: min(2, width)]
            base = edge_prefix + [col for col in center_order if col not in edge_prefix]
        positions = base
    elif layout == "regular_spaced":
        base = _evenly_spaced(width, count)
        if bias == "right":
            base = [width - 1 - col for col in reversed(base)]
        elif bias == "left":
            base = sorted(base)
        positions = base + [col for col in bias_order if col not in base]
    else:
        raise ValueError(f"unknown layout {layout!r}")
    result = []
    for col in positions:
        if col not in result:
            result.append(col)
        if len(result) == count:
            break
    if len(result) != count:
        raise AssertionError(f"layout returned {len(result)} columns, expected {count}")
    return sorted(result)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    width = ctx.draw_int_strict("grid_w", 2, 10)
    max_nz = min(width, 7, 30 // width)
    nz_count = ctx.draw_int_strict("nz_count", 1, max_nz)
    layout = ctx.draw_choice("nz_layout", NZ_LAYOUTS)
    color_dist = ctx.draw_choice("nz_color_dist", NZ_COLOR_DISTS)
    bias = ctx.draw_choice("nz_position_bias", NZ_BIASES)
    rng = ctx.draw_rng("placement")
    positions = _layout_positions(layout, bias, width, nz_count, rng)

    palette_count = nz_count if color_dist == "all_distinct" else (2 if color_dist == "two_colors" and nz_count > 1 else 1)
    palette = ctx.draw_distinct_colors("palette", n=palette_count, exclude={0})
    grid = full_grid(1, width, 0)
    for index, col in enumerate(positions):
        if color_dist == "all_distinct":
            color = palette[index]
        elif color_dist == "two_colors":
            color = palette[index % len(palette)]
        else:
            color = palette[0]
        grid[0][col] = color
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator constructed an invalid grid: {errors}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or len(grid) != 1 or type(grid[0]) is not list or not grid[0]:
        return ["expected one nonempty input row"]
    if len(grid[0]) > 30:
        return ["input width exceeds ARC limit 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for value in grid[0]):
        return ["grid cells must be exact integer colors 0..9"]
    width = len(grid[0])
    nz_count = sum(value != 0 for value in grid[0])
    errors = []
    if nz_count == 0:
        errors.append("expected at least one nonzero cell")
    if nz_count * width > 30:
        errors.append(f"nz*width={nz_count}*{width}={nz_count * width} exceeds 30")
    return errors


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid diagonal-projection input: " + "; ".join(errors))
    row = grid[0]
    width = len(row)
    nz_count = sum(value != 0 for value in row)
    size = nz_count * width
    return [
        [
            row[index] if 0 <= (index := col - (size - 1) + out_row) < width else 0
            for col in range(size)
        ]
        for out_row in range(size)
    ]
