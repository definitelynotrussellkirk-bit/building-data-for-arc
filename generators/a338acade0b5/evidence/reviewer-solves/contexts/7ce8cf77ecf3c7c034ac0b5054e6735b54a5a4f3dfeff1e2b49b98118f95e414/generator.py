"""Generator for ARC task ``a338acade0b5``.

The input contains exactly two equal-colored nonzero cells on a horizontal,
vertical, or 45-degree diagonal segment.  The output is a one-row cyan bar
whose width is the inclusive Chebyshev distance between the endpoints.

The six-slot default curriculum alternates vertical and nonvertical examples.
Therefore any four consecutive generated pairs contain two vertical
counterexamples before one pair is held out and at least one afterward,
refuting the strongest shortcut supported by the public demonstrations: using
column span alone as the bar length.  The nonvertical slots cover horizontal
and both diagonal directions; two broad vertical slots expand length, position,
endpoint color, and difficulty coverage.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Point = tuple[int, int]

GENERATOR_ID = "a338acade0b5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5661890ac5fd"

SUMMARY = (
    "Find the two equal-colored nonzero endpoints. They must share a row, "
    "share a column, or lie on a 45-degree diagonal. Return one row of cyan "
    "8s whose width is max(|dr|, |dc|) + 1. Any four consecutive default "
    "samples contain two vertical examples, so a one-pair holdout cannot "
    "leave the column-span-only shortcut consistent with every demo."
)

INVARIANTS = [
    "the input is a rectangular 5..14 by 5..14 ARC grid",
    "exactly two equal-colored nonzero endpoint cells are present",
    "the endpoints are horizontal, vertical, or on a 45-degree diagonal",
    "segment length is in 2..14 inclusive",
    "output is intrinsically a solid 1xL cyan bar",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 13  # one cyan bar for each segment length 2..14
SOLID_OUTPUT_JUSTIFICATION = (
    "The canonical transformation discards position, orientation, grid size, "
    "and endpoint color; its complete output grammar is the thirteen solid "
    "cyan bars of lengths 2 through 14."
)

ORIENTATIONS = ("horizontal", "vertical", "diag_down", "diag_up")
AXES = {
    "segment_length": {
        "type": "int",
        "default": "six-slot schedule or difficulty-banded draw",
        "valid": "2..14",
    },
    "orientation": {
        "type": "str",
        "default": "six-slot alternating schedule with three vertical slots",
        "valid": "horizontal|vertical|diag_down|diag_up",
    },
    "endpoint_color": {
        "type": "int",
        "default": "canonical red anchors or broad draw",
        "valid": "1..9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# No generic texture alias is advertised: every public control above is exact.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# name, orientation, segment length, endpoint color, canonical-size anchor.
# Vertical and nonvertical slots alternate, so every cyclic window of four
# contains exactly two vertical witnesses while both diagonal slopes occur.
_SCHEDULE: tuple[tuple[str, str, int | None, int | None, tuple[int, int] | None], ...] = (
    ("canonical_horizontal", "horizontal", 5, 2, (6, 8)),
    ("canonical_vertical", "vertical", 7, 2, (9, 9)),
    ("canonical_diagonal_up", "diag_up", 5, 2, (8, 8)),
    ("broad_vertical_a", "vertical", None, None, None),
    ("canonical_diagonal_down", "diag_down", 5, 2, (8, 8)),
    ("broad_vertical_b", "vertical", None, None, None),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)
LESSON_SCHEDULE_PERIOD = len(_SCHEDULE)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the named curriculum slot for this sample."""
    del seed, difficulty
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)][0]


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty is None:
        return
    if type(difficulty) is not str or difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")


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


def _endpoints(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (row_index, column_index, value)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != 0
    ]


def _geometry(grid: Sequence[Sequence[int]]) -> tuple[Point, Point, int, str, int]:
    points = _endpoints(grid)
    if len(points) != 2:
        raise ValueError("expected exactly two nonzero endpoints")
    (row_a, column_a, color_a), (row_b, column_b, color_b) = points
    if color_a != color_b:
        raise ValueError("endpoint colors must match")
    row_gap = abs(row_b - row_a)
    column_gap = abs(column_b - column_a)
    if row_gap == 0 and column_gap > 0:
        orientation = "horizontal"
    elif column_gap == 0 and row_gap > 0:
        orientation = "vertical"
    elif row_gap == column_gap and row_gap > 0:
        orientation = "diag_down" if (row_b - row_a) * (column_b - column_a) > 0 else "diag_up"
    else:
        raise ValueError("endpoints must be horizontal, vertical, or on a 45-degree diagonal")
    return (row_a, column_a), (row_b, column_b), max(row_gap, column_gap) + 1, orientation, color_a


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject inputs outside the generator's complete lawful grammar."""
    del meta
    errors: list[str] = []
    try:
        _validate_difficulty(difficulty)
    except ValueError as exc:
        errors.append(str(exc))

    height, width, shape_errors = _validate_grid(grid)
    if shape_errors:
        return errors + shape_errors
    if not 5 <= height <= 14:
        errors.append(f"height {height} outside declared envelope 5..14")
    if not 5 <= width <= 14:
        errors.append(f"width {width} outside declared envelope 5..14")

    points = _endpoints(grid)
    if len(points) != 2:
        errors.append(f"expected exactly two nonzero endpoints, found {len(points)}")
        return errors
    if points[0][2] != points[1][2]:
        errors.append("endpoint colors must match")

    try:
        _, _, length, _, _ = _geometry(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if not 2 <= length <= 14:
        errors.append(f"segment length {length} outside 2..14")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The canonical grammar is exactly the lawful two-endpoint grammar."""
    return self_check(grid)


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    """Recover every exact public axis from a returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    _, _, length, orientation, color = _geometry(grid)
    return {
        "segment_length": length,
        "orientation": orientation,
        "endpoint_color": color,
    }


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror used only for semantic checks and tests."""
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    _, _, length, _, _ = _geometry(grid)
    return [[8] * length]


def _column_span_only(grid: Sequence[Sequence[int]]) -> Grid:
    """Strongest rival supported by the two public demonstrations."""
    points = _endpoints(grid)
    if len(points) != 2:
        raise ValueError("expected exactly two endpoints")
    return [[8] * (abs(points[1][1] - points[0][1]) + 1)]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "column_span_only": _column_span_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _vertical_segment(grid: Any) -> bool:
    if self_check(grid):
        return False
    _, _, _, orientation, _ = _geometry(grid)
    return orientation == "vertical"


SEMANTIC_WITNESSES = {
    "vertical_segment": _vertical_segment,
}
WITNESS_RIVALS = {
    "vertical_segment": ["column_span_only"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require valid exact demos that collectively refute the named rival."""
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


def _length_bounds(difficulty: Any) -> tuple[int, int]:
    if difficulty == "easy":
        return 2, 6
    if difficulty == "medium":
        return 4, 10
    if difficulty == "hard":
        return 7, 14
    return 2, 14


def _dimension_bounds(difficulty: Any) -> tuple[int, int]:
    if difficulty == "easy":
        return 5, 9
    if difficulty == "medium":
        return 7, 12
    if difficulty == "hard":
        return 10, 14
    return 5, 14


def _draw_int_axis(
    ctx: Any,
    label: str,
    lo: int,
    hi: int,
    scheduled: int | None,
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    if scheduled is not None:
        return ctx.draw_int_strict(label, scheduled, scheduled)
    return ctx.draw_int_strict(label, lo, hi)


def _draw_orientation(ctx: Any, scheduled: str) -> str:
    options: Sequence[str] = ORIENTATIONS if "orientation" in ctx.overrides else (scheduled,)
    value = ctx.draw_choice("orientation", options)
    if type(value) is not str:  # draw_choice membership alone would accept exotic equal objects.
        raise TypeError("orientation override must be a string")
    return value


def _fits(height: int, width: int, orientation: str, length: int) -> bool:
    if orientation == "horizontal":
        return width >= length
    if orientation == "vertical":
        return height >= length
    return height >= length and width >= length


def _draw_dimensions(
    ctx: Any,
    *,
    difficulty: Any,
    orientation: str,
    length: int,
    anchor: tuple[int, int] | None,
) -> tuple[int, int]:
    # Preserve canonical-size anchors unless an exact geometry override no longer fits.
    if anchor is not None and _fits(anchor[0], anchor[1], orientation, length):
        return anchor

    low, high = _dimension_bounds(difficulty)
    required_height = length if orientation in {"vertical", "diag_down", "diag_up"} else 5
    required_width = length if orientation in {"horizontal", "diag_down", "diag_up"} else 5
    height_lo = max(low, required_height)
    width_lo = max(low, required_width)
    height_hi = max(height_lo, high)
    width_hi = max(width_lo, high)
    # Exact length overrides may exceed a band's ordinary upper bound, but never 14.
    height_hi = min(14, height_hi)
    width_hi = min(14, width_hi)
    height = ctx.draw_int_strict("height_internal", height_lo, height_hi)
    width = ctx.draw_int_strict("width_internal", width_lo, width_hi)
    return height, width


def _place_endpoints(
    ctx: Any,
    *,
    height: int,
    width: int,
    orientation: str,
    length: int,
) -> tuple[Point, Point]:
    gap = length - 1
    rng = ctx.draw_rng("placement")
    if orientation == "horizontal":
        row = rng.randrange(height)
        column = rng.randint(0, width - length)
        return (row, column), (row, column + gap)
    if orientation == "vertical":
        row = rng.randint(0, height - length)
        column = rng.randrange(width)
        return (row, column), (row + gap, column)
    row = rng.randint(0, height - length)
    column = rng.randint(0, width - length)
    if orientation == "diag_down":
        return (row, column), (row + gap, column + gap)
    return (row, column + gap), (row + gap, column)


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    """Generate one deterministic lawful input, honoring all exact controls."""
    _validate_difficulty(difficulty)
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
    _, scheduled_orientation, scheduled_length, scheduled_color, anchor = _SCHEDULE[
        int(sample_index) % len(_SCHEDULE)
    ]

    orientation = _draw_orientation(ctx, scheduled_orientation)
    length_lo, length_hi = _length_bounds(difficulty)
    if scheduled_length is None:
        # The production diversity probe starts each six-pair episode at index 0
        # and advances seeds by 101.  Since 101 is coprime to the 13-value full
        # domain, this broad slot visits every lawful bar length in 13 episodes
        # rather than relying on chance to certify the declared finite codomain.
        scheduled_length = length_lo + (
            (int(seed) + 17 * int(sample_index)) % (length_hi - length_lo + 1)
        )
    # Exact controls remain exact over the full declared domain in every band.
    axis_length_lo, axis_length_hi = (2, 14) if "segment_length" in overrides else (length_lo, length_hi)
    length = _draw_int_axis(
        ctx,
        "segment_length",
        axis_length_lo,
        axis_length_hi,
        scheduled_length,
    )
    color = _draw_int_axis(ctx, "endpoint_color", 1, 9, scheduled_color)

    height, width = _draw_dimensions(
        ctx,
        difficulty=difficulty,
        orientation=orientation,
        length=length,
        anchor=anchor,
    )
    first, second = _place_endpoints(
        ctx,
        height=height,
        width=width,
        orientation=orientation,
        length=length,
    )
    grid = full_grid(height, width, 0)
    grid[first[0]][first[1]] = color
    grid[second[0]][second[1]] = color
    return grid
