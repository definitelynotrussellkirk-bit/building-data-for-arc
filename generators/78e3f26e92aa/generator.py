"""Generator for 78e3f26e92aa (parent ARC slug 58e15b12).

Each input contains two separated, equal-height vertical green bars and two
separated, equal-height vertical cyan bars.  For each color, the bounding-box
height is the ray step size: above and below the pair, its left and right edges
move one column outward per block of ``bar_height`` rows.  The output contains
3 on green rays, 8 on cyan rays, 6 where they intersect, and 0 elsewhere.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78e3f26e92aa"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ed1ed1d0980e"

SUMMARY = (
    "A 22..24 by 17..20 color-0 grid contains two separated one-cell-wide "
    "vertical bars of equal height in green (3), plus an analogous pair in "
    "cyan (8), with the two color pairs vertically separated. Each pair emits "
    "two bidirectional step-rays from its outer bbox columns: the rays move "
    "one column outward per full bar-height of vertical distance. Output cells "
    "are green or cyan on one color's rays, magenta (6) at intersections, and "
    "0 elsewhere. Four canonical-anchor profiles are followed by four "
    "decorrelated companion profiles, covering both vertical orders, height-1 "
    "bars, and both intersection branches without locking independent axes."
)

INVARIANTS = [
    "the rectangular input uses only colors 0, 3, and 8",
    "each nonzero color has exactly two one-cell-wide filled vertical bars",
    "the two same-color bars have identical row spans and 1..4 blank columns between them",
    "green and cyan row spans are disjoint with 2..10 blank rows between them",
    "all four bars have at least a one-cell border margin",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical profile", "valid": "22..24"},
    "grid_w": {"type": "int", "default": "scheduled canonical profile", "valid": "17..20"},
    "green_height": {"type": "int", "default": "scheduled 1..4", "valid": "1..5"},
    "green_gap": {"type": "int", "default": "scheduled canonical gap", "valid": "1..4"},
    "cyan_height": {"type": "int", "default": "scheduled 1..5", "valid": "1..5"},
    "cyan_gap": {"type": "int", "default": "scheduled canonical gap", "valid": "1..4"},
    "vertical_gap": {"type": "int", "default": "scheduled 3,7,9,4", "valid": "2..10"},
    "color_order": {
        "type": "str",
        "default": "scheduled green_above/cyan_above",
        "valid": "green_above|cyan_above",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_PROFILE_NAMES = (
    "canonical_zero_intersection",
    "canonical_cyan_above_intersection",
    "canonical_height_one_intersection",
    "canonical_wide_gap_intersection",
    "decorrelated_green_gap",
    "decorrelated_vertical_gap",
    "decorrelated_height_gap",
    "decorrelated_wide_profile",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
_PROFILE_DEFAULTS = (
    # h, w, green height/gap, cyan height/gap, vertical gap, order
    (22, 18, 3, 1, 2, 2, 3, "green_above"),
    (23, 17, 3, 2, 4, 1, 7, "cyan_above"),
    (24, 19, 4, 3, 1, 1, 9, "green_above"),
    (24, 20, 3, 4, 5, 2, 4, "green_above"),
    # Same broad teaching branches, but crossed values break accidental 1:1 axes.
    (22, 18, 2, 4, 2, 1, 7, "cyan_above"),
    (23, 17, 5, 1, 4, 3, 4, "green_above"),
    (24, 19, 3, 2, 1, 4, 3, "cyan_above"),
    (24, 20, 4, 3, 5, 1, 9, "green_above"),
)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}


def schedule_profile(seed, sample_index, difficulty=None):
    """Eight profiles retain four canonical anchors and decorrelate axes."""
    del seed, difficulty
    return _PROFILE_NAMES[sample_index % len(_PROFILE_NAMES)]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer (not bool), got {type(seed).__name__}")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer (not bool), got {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    integer_axes = set(AXES) - {"color_order"}
    for name in integer_axes & set(overrides):
        if type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    if "color_order" in overrides and type(overrides["color_order"]) is not str:
        raise TypeError("color_order must be a string")


def _scheduled_int(ctx, overrides, label, default, lo, hi):
    """Keep the default schedule exact while exposing the full override domain."""
    if label in overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _scheduled_choice(ctx, overrides, label, default, options):
    if label in overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
                    cells.add(point)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        result.append(
            {
                "cells": frozenset(cells),
                "bbox": (r1, c1, r2, c2),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "filled": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
            }
        )
    return sorted(result, key=lambda item: item["bbox"])


def _pair_geometry(grid, color, errors):
    parts = _components(grid, color)
    if len(parts) != 2:
        errors.append(f"color {color} must have exactly two bars; found {len(parts)}")
        return None
    left, right = sorted(parts, key=lambda item: item["bbox"][1])
    for index, part in enumerate((left, right)):
        if not part["filled"] or part["width"] != 1:
            errors.append(
                f"color {color} component {index} must be a filled one-cell-wide vertical bar; "
                f"bbox={part['bbox']}"
            )
    if (left["bbox"][0], left["bbox"][2]) != (right["bbox"][0], right["bbox"][2]):
        errors.append(f"color {color} bars must share the same row span")
    if left["height"] != right["height"]:
        errors.append(f"color {color} bars must have equal heights")
    height = left["height"]
    if not 1 <= height <= 5:
        errors.append(f"color {color} bar height {height} outside 1..5")
    inner_gap = right["bbox"][1] - left["bbox"][1] - 1
    if not 1 <= inner_gap <= 4:
        errors.append(f"color {color} inner gap {inner_gap} outside 1..4")
    return {
        "row1": left["bbox"][0],
        "row2": left["bbox"][2],
        "height": height,
        "left_col": left["bbox"][1],
        "right_col": right["bbox"][1],
        "inner_gap": inner_gap,
    }


def _analyze(grid) -> tuple[dict[str, Any] | None, list[str]]:
    h, w, errors = _validate_grid(grid)
    if errors:
        return None, errors
    if not 22 <= h <= 24:
        errors.append(f"height {h} outside 22..24")
    if not 17 <= w <= 20:
        errors.append(f"width {w} outside 17..20")
    unexpected = sorted({value for row in grid for value in row} - {0, 3, 8})
    if unexpected:
        errors.append(f"unexpected colors outside {{0,3,8}}: {unexpected}")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    green = _pair_geometry(grid, 3, errors)
    cyan = _pair_geometry(grid, 8, errors)
    if green is None or cyan is None:
        return None, errors

    green_above = green["row2"] < cyan["row1"]
    cyan_above = cyan["row2"] < green["row1"]
    if not (green_above or cyan_above):
        errors.append("green and cyan row spans must be vertically disjoint")
        order = None
        vertical_gap = -1
    else:
        upper, lower = (green, cyan) if green_above else (cyan, green)
        order = "green_above" if green_above else "cyan_above"
        vertical_gap = lower["row1"] - upper["row2"] - 1
        if not 2 <= vertical_gap <= 10:
            errors.append(f"vertical gap {vertical_gap} outside 2..10")

    for color, pair in ((3, green), (8, cyan)):
        if pair["row1"] < 1 or pair["row2"] >= h - 1:
            errors.append(f"color {color} bars need a one-row outer margin")
        if pair["left_col"] < 1 or pair["right_col"] >= w - 1:
            errors.append(f"color {color} bars need a one-column outer margin")

    if errors:
        return None, errors
    return {
        "grid_h": h,
        "grid_w": w,
        "green_height": green["height"],
        "green_gap": green["inner_gap"],
        "cyan_height": cyan["height"],
        "cyan_gap": cyan["inner_gap"],
        "vertical_gap": vertical_gap,
        "color_order": order,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete four-bar input grammar and requested axes."""
    del difficulty
    observed, errors = _analyze(grid)
    if errors:
        return errors
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            for axis in AXES:
                if axis in requested and requested[axis] != observed[axis]:
                    errors.append(
                        f"requested {axis}={requested[axis]!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generator's lawful manifold deliberately matches the canonical envelope."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    observed, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    assert observed is not None
    return observed


def _bar_descriptor(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"color {color} is absent")
    row1 = min(r for r, _ in cells)
    row2 = max(r for r, _ in cells)
    left_col = min(c for _, c in cells)
    right_col = max(c for _, c in cells)
    return row1, row2 - row1 + 1, left_col, right_col


def _step_for_row(row1, bar_height, row):
    dr = row - row1
    return dr // bar_height if dr >= 0 else ((-dr + bar_height - 1) // bar_height)


def _bar_reaches(bar, row, col, *, unit_height=False, downward_only=False):
    row1, bar_height, left_col, right_col = bar
    if downward_only and row < row1:
        return False
    height = 1 if unit_height else bar_height
    step = _step_for_row(row1, height, row)
    return col == left_col - step or col == right_col + step


def _solve_with(grid, *, unit_height=False, downward_only=False, no_magenta=False):
    h, w, errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    green = _bar_descriptor(grid, 3)
    cyan = _bar_descriptor(grid, 8)
    output = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            has_green = _bar_reaches(
                green, r, c, unit_height=unit_height, downward_only=downward_only
            )
            has_cyan = _bar_reaches(
                cyan, r, c, unit_height=unit_height, downward_only=downward_only
            )
            if has_green and has_cyan:
                output[r][c] = 3 if no_magenta else 6
            elif has_green:
                output[r][c] = 3
            elif has_cyan:
                output[r][c] = 8
    return output


def rule_mirror(grid):
    """Exact Python mirror of the selected canonical Racket rule."""
    return _solve_with(grid)


def _unit_height_steps(grid):
    return _solve_with(grid, unit_height=True)


def _downward_only(grid):
    return _solve_with(grid, downward_only=True)


def _no_magenta_intersections(grid):
    return _solve_with(grid, no_magenta=True)


def _height_scaled_witness(grid):
    return _unit_height_steps(grid) != rule_mirror(grid)


def _bidirectional_witness(grid):
    return _downward_only(grid) != rule_mirror(grid)


def _magenta_witness(grid):
    return any(value == 6 for row in rule_mirror(grid) for value in row)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "unit_height_steps": _unit_height_steps,
    "downward_only": _downward_only,
    "no_magenta_intersections": _no_magenta_intersections,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable] = {
    "height_scaled_steps": _height_scaled_witness,
    "bidirectional_rays": _bidirectional_witness,
    "magenta_intersections": _magenta_witness,
}
WITNESS_RIVALS = {
    "height_scaled_steps": ["unit_height_steps"],
    "bidirectional_rays": ["downward_only"],
    "magenta_intersections": ["no_magenta_intersections"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared rival fits all demos but changes query."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one labeled demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled pair"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} is not a labeled pair")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons


def _reach_cells(h, w, row1, bar_height, left_col, right_col):
    cells = set()
    for row in range(h):
        step = _step_for_row(row1, bar_height, row)
        for col in (left_col - step, right_col + step):
            if 0 <= col < w:
                cells.add((row, col))
    return frozenset(cells)


def _draw_bars(h, w, green, cyan):
    grid = full_grid(h, w, 0)
    for color, pair in ((3, green), (8, cyan)):
        for col in (pair["left_col"], pair["right_col"]):
            for row in range(pair["row1"], pair["row1"] + pair["height"]):
                grid[row][col] = color
    return grid


def _placement_pools(
    h,
    w,
    green_height,
    green_gap,
    cyan_height,
    cyan_gap,
    vertical_gap,
    color_order,
):
    """Return cached compact placements partitioned by ray intersection.

    Override validation replays each axis case many times.  Geometry depends only
    on the eight axes, so rebuilding thousands of equivalent candidate records
    per seed is wasted work and previously made the contract matrix time out.
    """
    total_height = green_height + vertical_gap + cyan_height
    top_margin_max = h - total_height - 1
    if top_margin_max < 1:
        raise ValueError(
            "requested heights and vertical_gap do not leave the required outer row margins"
        )
    green_left_max = w - (green_gap + 2) - 1
    cyan_left_max = w - (cyan_gap + 2) - 1
    if green_left_max < 1 or cyan_left_max < 1:
        raise ValueError("requested gaps do not leave the required outer column margins")

    zero_intersection = []
    positive_intersection = []
    for top in range(1, top_margin_max + 1):
        if color_order == "green_above":
            green_row = top
            cyan_row = top + green_height + vertical_gap
        else:
            cyan_row = top
            green_row = top + cyan_height + vertical_gap

        green_reaches = {
            left: _reach_cells(h, w, green_row, green_height, left, left + green_gap + 1)
            for left in range(1, green_left_max + 1)
        }
        cyan_reaches = {
            left: _reach_cells(h, w, cyan_row, cyan_height, left, left + cyan_gap + 1)
            for left in range(1, cyan_left_max + 1)
        }
        for green_left, green_cells in green_reaches.items():
            for cyan_left, cyan_cells in cyan_reaches.items():
                placement = (green_row, green_left, cyan_row, cyan_left)
                if green_cells & cyan_cells:
                    positive_intersection.append(placement)
                else:
                    zero_intersection.append(placement)
    return tuple(zero_intersection), tuple(positive_intersection)


# Contract checks replay one axis tuple across many seeds.  A bounded cache keeps
# those calls O(1) while avoiding an unbounded cross-product in long processes.
_placement_pools = lru_cache(maxsize=64)(_placement_pools)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile_index = sample_index % len(_PROFILE_DEFAULTS)
    defaults = _PROFILE_DEFAULTS[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, overrides, "grid_h", defaults[0], 22, 24)
    w = _scheduled_int(ctx, overrides, "grid_w", defaults[1], 17, 20)
    green_height = _scheduled_int(ctx, overrides, "green_height", defaults[2], 1, 5)
    green_gap = _scheduled_int(ctx, overrides, "green_gap", defaults[3], 1, 4)
    cyan_height = _scheduled_int(ctx, overrides, "cyan_height", defaults[4], 1, 5)
    cyan_gap = _scheduled_int(ctx, overrides, "cyan_gap", defaults[5], 1, 4)
    vertical_gap = _scheduled_int(ctx, overrides, "vertical_gap", defaults[6], 2, 10)
    color_order = _scheduled_choice(
        ctx,
        overrides,
        "color_order",
        defaults[7],
        ("green_above", "cyan_above"),
    )

    zero_pool, positive_pool = _placement_pools(
        h,
        w,
        green_height,
        green_gap,
        cyan_height,
        cyan_gap,
        vertical_gap,
        color_order,
    )
    want_intersection = profile_index != 0
    preferred = positive_pool if want_intersection else zero_pool
    pool = preferred or (zero_pool + positive_pool)
    placement_rng = ctx.draw_rng("placement")
    base_index = placement_rng.randrange(len(pool))
    if difficulty is None:
        selected_index = base_index
    else:
        band_number = {"easy": 0, "medium": 1, "hard": 2}[difficulty]
        if len(pool) >= 3:
            offsets = (0, len(pool) // 3, (2 * len(pool)) // 3)
            selected_index = (base_index + offsets[band_number]) % len(pool)
        else:
            # Exact overrides stay constructive even when a requested semantic
            # branch has only one or two placements; default profiles have large
            # pools and still distinguish all three bands.
            selected_index = (base_index + band_number) % len(pool)
    green_row, green_left, cyan_row, cyan_left = pool[selected_index]
    green = {
        "row1": green_row,
        "height": green_height,
        "left_col": green_left,
        "right_col": green_left + green_gap + 1,
    }
    cyan = {
        "row1": cyan_row,
        "height": cyan_height,
        "left_col": cyan_left,
        "right_col": cyan_left + cyan_gap + 1,
    }
    return _draw_bars(h, w, green, cyan)
