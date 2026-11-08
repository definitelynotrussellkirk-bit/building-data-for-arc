"""Generator for ARC task 4a279b104523 — reflect content across an 8-axis.

A lawful input has one full horizontal color-8 row.  Every other nonzero cell
is a source cell, and the canonical transformation copies it to the same
column at equal distance on the opposite side of the axis while preserving the
input.  Sources may be above the axis, below it, or on both sides; generation
keeps each source's mirror target empty so every example visibly changes.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a279b104523"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "586c575373f0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find the unique full horizontal color-8 axis row. For every nonzero, "
    "non-8 source cell on either side, preserve it and copy the same color to "
    "the equal-distance row on the opposite side in the same column."
)

INVARIANTS = [
    "background is color 0",
    "exactly one complete color-8 row is the horizontal reflection axis",
    "the axis is interior and every source has an in-bounds mirror position",
    "there are 2..8 non-{0,8} source cells using ordinary ARC colors",
    "generated source cells have empty mirror targets so the rule is visible",
    "every three-sample teaching window covers above, below, and mixed sources",
    "every three-sample teaching window includes an off-center axis witness",
]

SOURCE_SIDES = ("above", "below", "both")
SCHEDULE_PROFILES = SOURCE_SIDES
_AXIS_SCHEDULE = ("center", "offcenter", "offcenter")
CONTENT_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted keyed choice with canonical anchors",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted keyed choice with canonical anchors",
        "valid": "4..11",
    },
    "n_cells": {
        "type": "int",
        "default": "difficulty-weighted keyed choice",
        "valid": "2..8",
    },
    "source_side": {
        "type": "str",
        "default": "three-slot above|below|both teaching schedule",
        "valid": "above|below|both",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    integer_domains = {
        "grid_h": (5, 14),
        "grid_w": (4, 11),
        "n_cells": (2, 8),
    }
    for name, (lo, hi) in integer_domains.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} override must be an integer, got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    if "source_side" in overrides:
        value = overrides["source_side"]
        if not isinstance(value, str) or value not in SOURCE_SIDES:
            raise ValueError(
                f"source_side override must be one of {SOURCE_SIDES}, got {value!r}"
            )


def _height_options(difficulty: str | None) -> list[int]:
    """Keep the full declared domain live while anchoring canonical scale."""
    domain = list(range(5, 15))
    canonical = [5, 6, 7]
    if difficulty == "easy":
        return canonical * 10 + domain
    if difficulty == "hard":
        return canonical * 10 + domain + [10, 11, 12, 13, 14] * 2
    return canonical * 8 + domain + [8, 9, 10]


def _width_options(difficulty: str | None) -> list[int]:
    domain = list(range(4, 12))
    canonical = [5, 6]
    if difficulty == "easy":
        return canonical * 12 + domain
    if difficulty == "hard":
        return canonical * 12 + domain + [8, 9, 10, 11] * 2
    return canonical * 10 + domain + [7, 8, 9]


def _cell_count_options(difficulty: str | None) -> list[int]:
    domain = list(range(2, 9))
    if difficulty == "easy":
        return domain + [2, 3, 4] * 3
    if difficulty == "hard":
        return domain + [5, 6, 7, 8] * 3
    return domain + [3, 4, 5, 6] * 2


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle source directions so every three-demo window teaches both ways."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _axis_schedule_mode(sample_index: int) -> str:
    """Put an off-center-axis witness in every consecutive three examples."""
    return _AXIS_SCHEDULE[int(sample_index) % len(_AXIS_SCHEDULE)]


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _axis_row(grid: list[list[int]]) -> int:
    rows = [index for index, row in enumerate(grid) if all(value == 8 for value in row)]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one full color-8 row, found {len(rows)}")
    return rows[0]


def _source_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row_index, column_index, value)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value not in (0, 8)
    ]


def _feasible_axes(height: int, width: int, n_cells: int) -> list[int]:
    return [
        axis
        for axis in range(1, height - 1)
        if min(axis, height - 1 - axis) * width >= n_cells
    ]


def _choose_colors(ctx, n_cells: int) -> list[int]:
    rng = ctx.draw_rng("content_colors")
    max_colors = min(4, n_cells)
    # Two content colors reproduce all canonical palette profiles; one, three,
    # and four remain frequent enough to prevent a fixed-palette shortcut.
    candidates = [1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 4]
    candidates = [count for count in candidates if count <= max_colors]
    color_count = rng.choice(candidates)
    colors = rng.sample(list(CONTENT_COLORS), color_count)
    assignments = colors[:]  # make every selected color observable
    assignments.extend(rng.choice(colors) for _ in range(n_cells - color_count))
    rng.shuffle(assignments)
    return assignments


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    axis_mode = _axis_schedule_mode(sample_index)
    height_options = _height_options(difficulty)
    if "grid_h" not in overrides and axis_mode == "offcenter":
        # For h >= 6, every declared width/count combination has a feasible
        # off-center axis. Exact h=5 overrides remain legal and fall back to
        # the only feasible axis when necessary.
        height_options = [height for height in height_options if height >= 6]
    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", _width_options(difficulty))
    n_cells = ctx.draw_choice("n_cells", _cell_count_options(difficulty))
    if "source_side" in overrides:
        source_side = ctx.draw_choice("source_side", SOURCE_SIDES)
    else:
        source_side = ctx.draw_choice(
            "source_side", (schedule_profile(seed, sample_index, difficulty),)
        )

    feasible_axes = _feasible_axes(height, width, n_cells)
    if not feasible_axes:  # Defensive: every declared override combination is feasible.
        raise ValueError(
            f"no axis can fit n_cells={n_cells} in a {height}x{width} grid"
        )
    if axis_mode == "offcenter":
        scheduled_axes = [axis for axis in feasible_axes if 2 * axis != height - 1]
    else:
        scheduled_axes = [axis for axis in feasible_axes if 2 * axis == height - 1]
    axis = ctx.draw_rng("axis_row").choice(scheduled_axes or feasible_axes)
    depth_limit = min(axis, height - 1 - axis)
    orbits = [
        (depth, column)
        for depth in range(1, depth_limit + 1)
        for column in range(width)
    ]
    chosen_orbits = ctx.draw_rng("source_orbits").sample(orbits, n_cells)

    if source_side == "above":
        orientations = [-1] * n_cells
    elif source_side == "below":
        orientations = [1] * n_cells
    else:
        orientation_rng = ctx.draw_rng("source_orientations")
        orientations = [-1, 1]
        orientations.extend(orientation_rng.choice((-1, 1)) for _ in range(n_cells - 2))
        orientation_rng.shuffle(orientations)

    grid = full_grid(height, width, 0)
    grid[axis] = [8] * width
    for (depth, column), orientation, color in zip(
        chosen_orbits, orientations, _choose_colors(ctx, n_cells)
    ):
        grid[axis + orientation * depth][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid reflection scene: " + "; ".join(errors))
    strict_errors = strict_canonical_like(grid)
    if strict_errors:
        raise RuntimeError(
            "constructed non-teaching reflection scene: " + "; ".join(strict_errors)
        )

    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_cells": n_cells,
        "source_side": source_side,
    }
    actual = observe_overrides(grid)
    if actual != expected:
        raise RuntimeError(f"axis observation mismatch: expected {expected}, got {actual}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical bidirectional reflection input grammar."""
    errors = _shape_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 14:
        errors.append(f"height must be in 5..14, got {height}")
    if not 4 <= width <= 11:
        errors.append(f"width must be in 4..11, got {width}")

    axis_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if all(value == 8 for value in row)
    ]
    if len(axis_rows) != 1:
        errors.append(
            f"expected exactly one full color-8 row, found {len(axis_rows)}"
        )
        return errors
    axis = axis_rows[0]
    if axis in (0, height - 1):
        errors.append(f"axis must be interior, got row {axis}")

    stray_eights = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        if row_index != axis
        for column_index, value in enumerate(row)
        if value == 8
    ]
    if stray_eights:
        errors.append(f"found {len(stray_eights)} color-8 cell(s) outside the axis row")

    sources = _source_cells(grid)
    if not 2 <= len(sources) <= 8:
        errors.append(f"expected 2..8 non-{{0,8}} source cells, found {len(sources)}")

    conflicts: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for row_index, column_index, value in sources:
        mirror_row = 2 * axis - row_index
        # Canonical train[1] deliberately includes a source whose reflected
        # row is outside the canvas. The authoritative rule preserves that
        # source and clips only the copy, so this is lawful task structure.
        if not 0 <= mirror_row < height:
            continue
        mirror_value = grid[mirror_row][column_index]
        if mirror_value not in (0, value):
            pair = tuple(sorted(((row_index, column_index), (mirror_row, column_index))))
            conflicts.add(pair)
    if conflicts:
        errors.append(
            f"{len(conflicts)} mirrored position pair(s) contain conflicting colors"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require a lawful, visibly-transforming teaching input."""
    errors = self_check(grid)
    if errors:
        return errors
    axis = _axis_row(grid)
    occupied_targets = 0
    for row_index, column_index, _ in _source_cells(grid):
        mirror_row = 2 * axis - row_index
        if 0 <= mirror_row < len(grid) and grid[mirror_row][column_index] != 0:
            occupied_targets += 1
    if occupied_targets:
        # A same-color mirrored pair is counted from both endpoints.  The exact
        # number is less important than making the non-teaching condition loud.
        errors.append(
            f"source cells must have empty mirror targets; found {occupied_targets} occupied target(s)"
        )
    return errors


def observe_overrides(grid: Any) -> dict[str, int | str]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    axis = _axis_row(grid)
    sources = _source_cells(grid)
    above = any(row_index < axis for row_index, _, _ in sources)
    below = any(row_index > axis for row_index, _, _ in sources)
    if above and below:
        source_side = "both"
    elif above:
        source_side = "above"
    elif below:
        source_side = "below"
    else:
        source_side = "none"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(sources),
        "source_side": source_side,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful grid: " + "; ".join(errors))
    out = deepcopy(grid)
    axis = _axis_row(grid)
    for row_index, column_index, value in _source_cells(grid):
        mirror_row = 2 * axis - row_index
        if 0 <= mirror_row < len(grid):
            out[mirror_row][column_index] = value
    return out


def _above_only_rival(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut learned from one-way examples: only reflect sources above."""
    out = deepcopy(grid)
    axis = _axis_row(grid)
    for row_index, column_index, value in _source_cells(grid):
        if row_index < axis:
            mirror_row = 2 * axis - row_index
            if 0 <= mirror_row < len(grid):
                out[mirror_row][column_index] = value
    return out


def _grid_center_rival(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut that ignores the color-8 row and reflects through grid center."""
    out = deepcopy(grid)
    height = len(grid)
    for row_index, column_index, value in _source_cells(grid):
        mirror_row = height - 1 - row_index
        if 0 <= mirror_row < height:
            out[mirror_row][column_index] = value
    return out


SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "above_only": _above_only_rival,
    "grid_center": _grid_center_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _below_source_witness(grid: list[list[int]]) -> bool:
    try:
        axis = _axis_row(grid)
        has_below = any(row_index > axis for row_index, _, _ in _source_cells(grid))
        return has_below and _above_only_rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _off_center_axis_witness(grid: list[list[int]]) -> bool:
    try:
        axis = _axis_row(grid)
        return (
            2 * axis != len(grid) - 1
            and _grid_center_rival(grid) != rule_mirror(grid)
        )
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "below_source": _below_source_witness,
    "off_center_axis": _off_center_axis_witness,
}
WITNESS_RIVALS = {
    "below_source": ["above_only"],
    "off_center_axis": ["grid_center"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut survives every demo but fails query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output does not match reflection across the 8-axis")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons
