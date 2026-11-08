"""Generator for ARC task bf89d739 / d8111f3f714d.

The input contains one uniquely aligned pair of red (2) cells.  That pair is
its trunk: the oracle joins the pair with green (3).  Every other red is a
branch strictly inside the trunk span and at least two cells away from the
trunk line; the oracle joins each branch perpendicularly to the trunk.

Ordinary sequential samples alternate vertical and horizontal trunks.  Branch
counts cover 1..5 (including the five-branch canonical case), and layouts place
multi-branch scenes on both sides of the trunk so one-sided or fixed-position
shortcuts do not explain the lesson.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d8111f3f714d"
TASK_ID = "d8111f3f714d"
VERSION = "3.0.0"
RULE_HASH = "2a9d26bd68ef"

SUMMARY = (
    "On a 0-background grid, the unique pair of red (2) cells sharing a row "
    "or column forms a trunk. Join the trunk endpoints with green (3), then "
    "connect every remaining red perpendicularly to the trunk in green. "
    "Generated scenes vary dimensions, orientation, trunk placement/span, "
    "branch count (1..5), branch rows/columns, and both branch sides."
)

INVARIANTS = [
    "exactly one pair of red cells shares a row or column; that pair is the trunk",
    "there are 1..5 branch reds at distinct rows and distinct columns",
    "every branch lies strictly inside the trunk span and off the trunk line",
    "every branch is at least two cells from the trunk, so its connector is visible",
    "scenes with at least two branches place branches on both sides of the trunk",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "10..24",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "10..24",
    },
    "orientation": {
        "type": "enum",
        "default": "alternating sample_index schedule",
        "valid": "v|h",
    },
    "n_branches": {
        "type": "int",
        "default": "difficulty-linked sample_index schedule",
        "valid": "1..5",
    },
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_ORIENTATIONS = ("v", "h")
_BRANCH_SCHEDULES = {
    None: (1, 2, 3, 4, 5),
    "easy": (1, 2),
    "medium": (2, 3, 4),
    "hard": (3, 4, 5),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "n_branches"):
        value = overrides.get(label)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{label} must be an integer")
    orientation = overrides.get("orientation")
    if orientation is not None and orientation not in _ORIENTATIONS:
        raise ValueError("orientation must be 'v' or 'h'")


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], sample_index: int) -> str:
    """Record a deterministic lesson schedule while honoring exact overrides."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    scheduled = options[sample_index % len(options)]
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_branch_count(ctx, difficulty: Any, sample_index: int) -> int:
    if ctx.overrides.get("n_branches") is not None:
        return ctx.draw_int("n_branches", 1, 5)
    schedule = _BRANCH_SCHEDULES[difficulty]
    scheduled = schedule[sample_index % len(schedule)]
    return ctx.draw_int("n_branches", scheduled, scheduled)


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty rectangle"]}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"]}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular with non-empty rows"]}

    height = len(grid)
    if not 10 <= height <= 24 or not 10 <= width <= 24:
        errors.append("grid dimensions must each be within 10..24")

    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or value not in (0, 2)
    ]
    if bad_cells:
        errors.append("input palette must contain only integer colors 0 and 2")
        return {
            "errors": errors,
            "grid_h": height,
            "grid_w": width,
            "bad_cells": bad_cells[:8],
        }

    reds = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    n_branches = len(reds) - 2
    if not 1 <= n_branches <= 5:
        errors.append(f"expected 3..7 red cells (1..5 branches), found {len(reds)}")

    sharing_pairs = [
        (first, second)
        for index, first in enumerate(reds)
        for second in reds[index + 1 :]
        if first[0] == second[0] or first[1] == second[1]
    ]
    if len(sharing_pairs) != 1:
        errors.append(
            "expected exactly one row/column-sharing red pair, "
            f"found {len(sharing_pairs)}"
        )
        return {
            "errors": errors,
            "grid_h": height,
            "grid_w": width,
            "reds": reds,
            "sharing_pairs": sharing_pairs,
            "n_branches": n_branches,
        }

    endpoint_a, endpoint_b = sharing_pairs[0]
    branches = [point for point in reds if point not in (endpoint_a, endpoint_b)]
    if endpoint_a[1] == endpoint_b[1]:
        orientation = "v"
        trunk_line = endpoint_a[1]
        start, end = sorted((endpoint_a[0], endpoint_b[0]))
        major_coords = [row for row, _col in branches]
        minor_coords = [col for _row, col in branches]
    else:
        orientation = "h"
        trunk_line = endpoint_a[0]
        start, end = sorted((endpoint_a[1], endpoint_b[1]))
        major_coords = [col for _row, col in branches]
        minor_coords = [row for row, _col in branches]

    trunk_span = end - start
    if trunk_span < 2:
        errors.append("trunk endpoints must leave at least one interior cell")
    if any(not start < coord < end for coord in major_coords):
        errors.append("every branch must lie strictly inside the trunk span")
    if any(coord == trunk_line for coord in minor_coords):
        errors.append("branch reds must not lie on the trunk line")
    if any(abs(coord - trunk_line) < 2 for coord in minor_coords):
        errors.append("every branch must be at least two cells from the trunk line")
    if len(major_coords) != len(set(major_coords)):
        errors.append("branch coordinates along the trunk must be distinct")
    if len(minor_coords) != len(set(minor_coords)):
        errors.append("branch coordinates across the trunk must be distinct")

    side_support = {
        "negative": sum(coord < trunk_line for coord in minor_coords),
        "positive": sum(coord > trunk_line for coord in minor_coords),
    }
    if len(branches) >= 2 and not all(side_support.values()):
        errors.append("multi-branch scenes must place branches on both sides of the trunk")

    return {
        "errors": sorted(set(errors)),
        "grid_h": height,
        "grid_w": width,
        "reds": reds,
        "trunk": (endpoint_a, endpoint_b),
        "orientation": orientation,
        "trunk_line": trunk_line,
        "trunk_start": start,
        "trunk_end": end,
        "trunk_span": trunk_span,
        "branches": branches,
        "n_branches": len(branches),
        "side_support": side_support,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding trunk-and-branch scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "orientation": analysis["orientation"],
        "n_branches": analysis["n_branches"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python parity mirror; canonical Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))

    output = [list(row) for row in grid]
    endpoint_a, endpoint_b = analysis["trunk"]
    if analysis["orientation"] == "v":
        trunk_col = endpoint_a[1]
        row_1, row_2 = sorted((endpoint_a[0], endpoint_b[0]))
        for row in range(row_1 + 1, row_2):
            output[row][trunk_col] = 3
        for row, col in analysis["branches"]:
            for connector_col in range(min(col, trunk_col) + 1, max(col, trunk_col)):
                output[row][connector_col] = 3
    else:
        trunk_row = endpoint_a[0]
        col_1, col_2 = sorted((endpoint_a[1], endpoint_b[1]))
        for col in range(col_1 + 1, col_2):
            output[trunk_row][col] = 3
        for row, col in analysis["branches"]:
            for connector_row in range(min(row, trunk_row) + 1, max(row, trunk_row)):
                output[connector_row][col] = 3
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, nondegenerate trunk-and-branches input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = ctx.draw_int_diff("grid_h", 10, 24)
    width = ctx.draw_int_diff("grid_w", 10, 24)
    orientation = _scheduled_choice(ctx, "orientation", _ORIENTATIONS, sample_index)
    n_branches = _scheduled_branch_count(ctx, difficulty, sample_index)
    rng = ctx.draw_rng("layout")

    major_size = height if orientation == "v" else width
    minor_size = width if orientation == "v" else height
    minimum_span = n_branches + 1
    if major_size - 1 < minimum_span:
        raise ValueError(
            f"{orientation} orientation needs major dimension >= {minimum_span + 1} "
            f"for {n_branches} branches"
        )

    trunk_span = rng.randint(minimum_span, major_size - 1)
    trunk_start = rng.randint(0, major_size - trunk_span - 1)
    trunk_end = trunk_start + trunk_span
    trunk_line = rng.randint(2, minor_size - 3)

    interior_positions = list(range(trunk_start + 1, trunk_end))
    branch_major = rng.sample(interior_positions, n_branches)

    negative_side = list(range(0, trunk_line - 1))
    positive_side = list(range(trunk_line + 2, minor_size))
    rng.shuffle(negative_side)
    rng.shuffle(positive_side)
    if not negative_side or not positive_side:
        raise ValueError("grid leaves no visible connector position on both trunk sides")

    if n_branches == 1:
        branch_minor = [rng.choice(negative_side + positive_side)]
    else:
        branch_minor = [negative_side.pop(), positive_side.pop()]
        remaining = negative_side + positive_side
        rng.shuffle(remaining)
        branch_minor.extend(remaining[: n_branches - 2])
    rng.shuffle(branch_minor)

    grid = full_grid(height, width, 0)
    if orientation == "v":
        grid[trunk_start][trunk_line] = 2
        grid[trunk_end][trunk_line] = 2
        for row, col in zip(branch_major, branch_minor):
            grid[row][col] = 2
    else:
        grid[trunk_line][trunk_start] = 2
        grid[trunk_line][trunk_end] = 2
        for col, row in zip(branch_major, branch_minor):
            grid[row][col] = 2

    errors = self_check(grid)
    if errors:
        raise AssertionError("internal generator invariant failure: " + "; ".join(errors))
    return grid
