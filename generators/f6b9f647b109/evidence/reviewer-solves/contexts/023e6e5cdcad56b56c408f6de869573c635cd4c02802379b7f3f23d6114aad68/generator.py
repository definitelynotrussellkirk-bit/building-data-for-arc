"""Generator for ARC task ``992798f6`` / content hash ``f6b9f647b109``.

The input is a zero-background grid with one red (2) endpoint and one blue (1)
endpoint.  Starting at red, the rule takes one diagonal step toward blue,
continues along the dominant row/column axis, then finishes with diagonal
steps; intermediate cells become green (3) and both endpoints remain.

The sixteen-slot schedule is deliberately lesson-level rather than merely
marginal.  Any four consecutive samples contain row- and column-dominant
examples, compact and extended separations, every endpoint direction, and at
least two canonical-size anchors.  Across one period, every direction is
crossed with every axis/distance pair and the query slot recombines the repeated
direction.  This refutes natural rivals without teaching direction-conditioned
axis or distance shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Point = tuple[int, int]

GENERATOR_ID = "f6b9f647b109"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "b267fa2de39d"

SUMMARY = (
    "On a 0-background grid, find the unique red (2) and blue (1) endpoints. "
    "From red toward blue, take one diagonal step, then the required straight "
    "steps along the dominant axis, then the remaining diagonal steps. Paint "
    "only intermediate path cells green (3); preserve both endpoints. Every "
    "four consecutive generated demonstrations cover both dominant axes, "
    "compact and extended separations, all four directions, and at least two "
    "canonical-size anchors. Across sixteen slots, every direction crosses "
    "every axis/distance pair and the query recombines its repeated direction."
)

INVARIANTS = [
    "the input is a rectangular 6..26 by 6..26 ARC grid using only colors 0, 1, and 2",
    "there is exactly one red endpoint and exactly one blue endpoint",
    "the endpoints differ in both row and column and have Chebyshev distance at least 2",
    "ordinary generated paths are unequal-axis cases, so the straight middle segment is visible",
    "the factor-crossed schedule removes default direction-to-axis/distance locks",
    "the Racket rule is the sole output authority; rule_mirror is test-only parity logic",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

MAJOR_AXES = ("row", "column")
DISTANCE_PROFILES = ("compact", "extended")
DIRECTIONS = ("down_left", "up_left", "down_right", "up_right")

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical anchor or band draw", "valid": "6..26"},
    "grid_w": {"type": "int", "default": "scheduled canonical anchor or band draw", "valid": "6..26"},
    "major_axis": {"type": "str", "default": "sixteen-slot factor-crossed schedule", "valid": "row|column"},
    "distance_profile": {
        "type": "str",
        "default": "sixteen-slot factor-crossed schedule",
        "valid": "compact|extended",
    },
    "direction": {
        "type": "str",
        "default": "sixteen-slot factor-crossed schedule",
        "valid": "down_left|up_left|down_right|up_right",
    },
}

# Every Cartesian combination of the declared exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# The direction order has period four, while axis/distance assignments rotate
# over four blocks.  Consequently every sliding four-sample lesson contains all
# directions and both values of each binary semantic axis; over sixteen slots,
# each direction appears with all four axis/distance combinations.  The fifth
# (query) slot keeps the first demo's direction but changes its axis/distance
# pair, so a lesson cannot succeed by copying a direction-conditioned template.
_SCHEDULE = (
    ("s00_down_left_row_extended", "row", "extended", "down_left"),
    ("s01_up_left_column_extended", "column", "extended", "up_left"),
    ("s02_down_right_row_compact", "row", "compact", "down_right"),
    ("s03_up_right_column_compact", "column", "compact", "up_right"),
    ("s04_down_left_row_compact", "row", "compact", "down_left"),
    ("s05_up_left_row_extended", "row", "extended", "up_left"),
    ("s06_down_right_column_compact", "column", "compact", "down_right"),
    ("s07_up_right_column_extended", "column", "extended", "up_right"),
    ("s08_down_left_column_compact", "column", "compact", "down_left"),
    ("s09_up_left_row_compact", "row", "compact", "up_left"),
    ("s10_down_right_column_extended", "column", "extended", "down_right"),
    ("s11_up_right_row_extended", "row", "extended", "up_right"),
    ("s12_down_left_column_extended", "column", "extended", "down_left"),
    ("s13_up_left_column_compact", "column", "compact", "up_left"),
    ("s14_down_right_row_extended", "row", "extended", "down_right"),
    ("s15_up_right_row_compact", "row", "compact", "up_right"),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)

# Nine anchors break the former direction-to-scale coupling while guaranteeing
# at least two canonical-size examples in every cyclic four-sample window.
_CANONICAL_ANCHOR_MASK = (
    True, True, False, True,
    False, True, True, False,
    True, False, True, False,
    True, True, False, False,
)

_CANONICAL_DIMS = ((15, 16), (15, 12), (16, 16), (13, 12))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the semantic slot used by a generated sample."""
    del seed, difficulty
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)][0]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _endpoints(grid: Sequence[Sequence[int]]) -> tuple[list[Point], list[Point]]:
    reds: list[Point] = []
    blues: list[Point] = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 2:
                reds.append((row_index, column_index))
            elif value == 1:
                blues.append((row_index, column_index))
    return reds, blues


def _geometry(grid: Sequence[Sequence[int]]) -> tuple[Point, Point, int, int]:
    reds, blues = _endpoints(grid)
    if len(reds) != 1 or len(blues) != 1:
        raise ValueError("expected exactly one red and one blue endpoint")
    red, blue = reds[0], blues[0]
    return red, blue, abs(blue[0] - red[0]), abs(blue[1] - red[1])


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, oracle-hiding, and shortcut-compatible inputs."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 6 <= height <= 26:
        errors.append(f"height {height} outside declared envelope 6..26")
    if not 6 <= width <= 26:
        errors.append(f"width {width} outside declared envelope 6..26")

    unexpected = sorted({value for row in grid for value in row} - {0, 1, 2})
    if unexpected:
        errors.append(f"input colors outside {{0,1,2}}: {unexpected}")

    reds, blues = _endpoints(grid)
    if len(reds) != 1:
        errors.append(f"expected exactly one red endpoint, found {len(reds)}")
    if len(blues) != 1:
        errors.append(f"expected exactly one blue endpoint, found {len(blues)}")
    if len(reds) != 1 or len(blues) != 1:
        return errors

    red, blue = reds[0], blues[0]
    row_gap = abs(blue[0] - red[0])
    column_gap = abs(blue[1] - red[1])
    if row_gap == 0 or column_gap == 0:
        errors.append("endpoints must differ in both row and column")
    if max(row_gap, column_gap) < 2:
        errors.append("endpoint Chebyshev distance must be at least 2")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Empirical canonical envelope shared by the ten shipped source inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in _CANONICAL_DIMS:
        reasons.append(
            f"dimensions {dimensions[0]}x{dimensions[1]} are outside canonical profiles {_CANONICAL_DIMS}"
        )
    _, _, row_gap, column_gap = _geometry(grid)
    if row_gap == column_gap:
        reasons.append("canonical examples all have a visible dominant axis")
    return reasons


def _direction(red: Point, blue: Point) -> str:
    vertical = "down" if blue[0] > red[0] else "up"
    horizontal = "right" if blue[1] > red[1] else "left"
    return f"{vertical}_{horizontal}"


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    red, blue, row_gap, column_gap = _geometry(grid)
    if row_gap > column_gap:
        major_axis = "row"
    elif column_gap > row_gap:
        major_axis = "column"
    else:
        major_axis = "balanced"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "major_axis": major_axis,
        "distance_profile": "compact" if max(row_gap, column_gap) <= 3 else "extended",
        "direction": _direction(red, blue),
    }


def _sign(delta: int) -> int:
    return 1 if delta > 0 else -1


def _true_path_cells(red: Point, blue: Point) -> list[Point]:
    """Intermediate cells for the canonical red-to-blue phase order."""
    red_row, red_column = red
    blue_row, blue_column = blue
    row_step = _sign(blue_row - red_row)
    column_step = _sign(blue_column - red_column)
    row_gap = abs(blue_row - red_row)
    column_gap = abs(blue_column - red_column)
    max_gap = max(row_gap, column_gap)
    straight_steps = max_gap - min(row_gap, column_gap)
    row_dominant = row_gap > column_gap

    cells: list[Point] = []
    row, column = red
    for step in range(1, max_gap):
        if step == 1:
            row += row_step
            column += column_step
        elif step <= 1 + straight_steps:
            if row_dominant:
                row += row_step
            else:
                column += column_step
        else:
            row += row_step
            column += column_step
        cells.append((row, column))
    return cells


def _paint_path(grid: Sequence[Sequence[int]], cells: Sequence[Point]) -> Grid:
    out = [list(row) for row in grid]
    for row, column in cells:
        out[row][column] = 3
    return out


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; Racket remains output authority."""
    red, blue, _, _ = _geometry(grid)
    return _paint_path(grid, _true_path_cells(red, blue))


def _segment_path(
    grid: Sequence[Sequence[int]], *, diagonal_first: bool, reverse_roles: bool = False
) -> Grid:
    red, blue, row_gap, column_gap = _geometry(grid)
    if reverse_roles:
        red, blue = blue, red
    row_step = _sign(blue[0] - red[0])
    column_step = _sign(blue[1] - red[1])
    diagonal_steps = min(row_gap, column_gap)
    straight_steps = abs(row_gap - column_gap)
    row_dominant = row_gap > column_gap
    segments = (
        (("diagonal", diagonal_steps), ("straight", straight_steps))
        if diagonal_first
        else (("straight", straight_steps), ("diagonal", diagonal_steps))
    )
    row, column = red
    cells: list[Point] = []
    for kind, count in segments:
        for _ in range(count):
            if kind == "diagonal":
                row += row_step
                column += column_step
            elif row_dominant:
                row += row_step
            else:
                column += column_step
            if (row, column) != blue:
                cells.append((row, column))
    return _paint_path(grid, cells)


def _reverse_true_rule(grid: Sequence[Sequence[int]]) -> Grid:
    red, blue, _, _ = _geometry(grid)
    return _paint_path(grid, _true_path_cells(blue, red))


def _manhattan_row_then_column(grid: Sequence[Sequence[int]]) -> Grid:
    red, blue, _, _ = _geometry(grid)
    row, column = red
    cells: list[Point] = []
    while row != blue[0]:
        row += _sign(blue[0] - row)
        if (row, column) != blue:
            cells.append((row, column))
    while column != blue[1]:
        column += _sign(blue[1] - column)
        if (row, column) != blue:
            cells.append((row, column))
    return _paint_path(grid, cells)


def _bresenham_like(grid: Sequence[Sequence[int]]) -> Grid:
    red, blue, row_gap, column_gap = _geometry(grid)
    steps = max(row_gap, column_gap)
    cells = []
    for step in range(1, steps):
        fraction = step / steps
        row = round(red[0] + (blue[0] - red[0]) * fraction)
        column = round(red[1] + (blue[1] - red[1]) * fraction)
        cells.append((row, column))
    return _paint_path(grid, cells)


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "reverse_blue_to_red_roles": _reverse_true_rule,
    "all_diagonals_then_straight": lambda grid: _segment_path(
        grid, diagonal_first=True
    ),
    "straight_then_all_diagonals": lambda grid: _segment_path(
        grid, diagonal_first=False
    ),
    "manhattan_row_then_column": _manhattan_row_then_column,
    "bresenham_even_spacing": _bresenham_like,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _row_branch(grid: Any) -> bool:
    if self_check(grid):
        return False
    _, _, row_gap, column_gap = _geometry(grid)
    return row_gap > column_gap


def _column_branch(grid: Any) -> bool:
    if self_check(grid):
        return False
    _, _, row_gap, column_gap = _geometry(grid)
    return column_gap > row_gap


def _compact_branch(grid: Any) -> bool:
    if self_check(grid):
        return False
    _, _, row_gap, column_gap = _geometry(grid)
    return max(row_gap, column_gap) == 3


def _extended_branch(grid: Any) -> bool:
    if self_check(grid):
        return False
    _, _, row_gap, column_gap = _geometry(grid)
    return max(row_gap, column_gap) >= 5 and min(row_gap, column_gap) >= 3


SEMANTIC_WITNESSES = {
    "row_dominant_path": _row_branch,
    "column_dominant_path": _column_branch,
    "compact_phase_order": _compact_branch,
    "extended_phase_order": _extended_branch,
    "red_blue_roles_refute_reverse": lambda grid: _valid_and_refutes(
        grid, "reverse_blue_to_red_roles"
    ),
    "middle_phase_refutes_diagonal_first": lambda grid: _valid_and_refutes(
        grid, "all_diagonals_then_straight"
    ),
    "first_diagonal_refutes_straight_first": lambda grid: _valid_and_refutes(
        grid, "straight_then_all_diagonals"
    ),
    "non_manhattan_path": lambda grid: _valid_and_refutes(
        grid, "manhattan_row_then_column"
    ),
    "clustered_straights_refute_bresenham": lambda grid: _valid_and_refutes(
        grid, "bresenham_even_spacing"
    ),
}

# These four witnesses measure positive curriculum branch coverage.  They do
# not claim that every firing refutes one fixed rival; the named competitors
# are instead checked across each complete lesson by ``lesson_identifiable``.
BRANCH_WITNESSES = {
    "row_dominant_path",
    "column_dominant_path",
    "compact_phase_order",
    "extended_phase_order",
}

WITNESS_RIVALS = {
    "red_blue_roles_refute_reverse": ["reverse_blue_to_red_roles"],
    "middle_phase_refutes_diagonal_first": ["all_diagonals_then_straight"],
    "first_diagonal_refutes_straight_first": ["straight_then_all_diagonals"],
    "non_manhattan_path": ["manhattan_row_then_column"],
    "clustered_straights_refute_bresenham": ["bresenham_even_spacing"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require exact demos that collectively refute every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")

    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def _draw_axis(ctx: Any, label: str, options: Sequence[str], scheduled: str) -> str:
    draw_options = options if label in ctx.overrides else (scheduled,)
    return str(ctx.draw_choice(label, draw_options))


def _draw_dimension(ctx: Any, label: str, lo: int, hi: int, anchor: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 6, 26)
    if anchor is not None:
        return ctx.draw_int(label, anchor, anchor)
    return ctx.draw_int(label, lo, hi)


def _band_bounds(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (8, 12), (8, 12)
    if difficulty == "hard":
        return (14, 24), (14, 24)
    return (11, 16), (11, 16)


def _gaps(
    ctx: Any,
    *,
    height: int,
    width: int,
    major_axis: str,
    distance_profile: str,
) -> tuple[int, int]:
    if distance_profile == "compact":
        major_gap, minor_gap = 3, 2
    else:
        major_limit = height - 1 if major_axis == "row" else width - 1
        minor_limit = width - 1 if major_axis == "row" else height - 1
        major_gap = ctx.draw_int("major_gap_internal", 5, major_limit)
        minor_gap = ctx.draw_int(
            "minor_gap_internal", 3, min(minor_limit, major_gap - 2)
        )
    return (
        (major_gap, minor_gap)
        if major_axis == "row"
        else (minor_gap, major_gap)
    )


def _place_endpoints(
    ctx: Any,
    *,
    height: int,
    width: int,
    row_gap: int,
    column_gap: int,
    direction: str,
) -> tuple[Point, Point]:
    rng = ctx.draw_rng("placement")
    low_row = rng.randint(0, height - row_gap - 1)
    low_column = rng.randint(0, width - column_gap - 1)
    high_row = low_row + row_gap
    high_column = low_column + column_gap
    mapping = {
        "down_right": ((low_row, low_column), (high_row, high_column)),
        "down_left": ((low_row, high_column), (high_row, low_column)),
        "up_right": ((high_row, low_column), (low_row, high_column)),
        "up_left": ((high_row, high_column), (low_row, low_column)),
    }
    return mapping[direction]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    _, scheduled_major, scheduled_distance, scheduled_direction = _SCHEDULE[
        int(sample_index) % len(_SCHEDULE)
    ]

    major_axis = _draw_axis(ctx, "major_axis", MAJOR_AXES, scheduled_major)
    distance_profile = _draw_axis(
        ctx, "distance_profile", DISTANCE_PROFILES, scheduled_distance
    )
    direction = _draw_axis(ctx, "direction", DIRECTIONS, scheduled_direction)

    (height_lo, height_hi), (width_lo, width_hi) = _band_bounds(difficulty)
    anchor_dims: tuple[int, int] | None = None
    if not any(key in overrides for key in ("grid_h", "grid_w")):
        slot = int(sample_index) % len(_SCHEDULE)
        if _CANONICAL_ANCHOR_MASK[slot]:
            # Anchor status rotates independently of direction.  The keyed
            # choice is deterministic and does not touch process-global RNG.
            anchor_dims = ctx.draw_choice("canonical_dimensions", _CANONICAL_DIMS)

    height = _draw_dimension(
        ctx, "grid_h", height_lo, height_hi, anchor_dims[0] if anchor_dims else None
    )
    width = _draw_dimension(
        ctx, "grid_w", width_lo, width_hi, anchor_dims[1] if anchor_dims else None
    )

    row_gap, column_gap = _gaps(
        ctx,
        height=height,
        width=width,
        major_axis=major_axis,
        distance_profile=distance_profile,
    )
    red, blue = _place_endpoints(
        ctx,
        height=height,
        width=width,
        row_gap=row_gap,
        column_gap=column_gap,
        direction=direction,
    )
    grid = full_grid(height, width, 0)
    grid[red[0]][red[1]] = 2
    grid[blue[0]][blue[1]] = 1
    return grid
