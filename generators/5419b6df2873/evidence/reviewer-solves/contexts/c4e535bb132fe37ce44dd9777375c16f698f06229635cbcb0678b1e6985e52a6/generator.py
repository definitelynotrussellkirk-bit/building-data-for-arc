"""Constructive generator for ARC task 5419b6df2873.

A nonzero cell in the first row is a column marker.  The authoritative output
starts from a fresh zero grid and fills every marked column with its marker
color.  In particular, unrelated lower-row input cells are erased rather than
copied to the output.

The canonical examples contain no lower-row content, so the strongest simple
shortcut is to copy the input and then fill the marked columns.  Every ordinary
generated sample therefore contains an erasure witness: one lower-row colored
cell in an unmarked column.  Its color is reused from the marker palette so the
five-slot schedule still matches every canonical (height, width, palette-size)
profile exactly.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5419b6df2873"
TASK_ID = GENERATOR_ID
RULE_HASH = "72e1b062f409"
VERSION = "3.0.0"

SUMMARY = (
    "The top row contains 2-5 distinct nonzero markers. Build a fresh zero "
    "grid and fill each marked column with its marker color, erasing all "
    "unrelated lower-row input content. Every generated sample includes one "
    "lower-row erasure witness in an unmarked column."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input is a rectangular 5..9 by 6..11 ARC grid",
    "the top row has 2..5 markers in distinct columns and distinct colors",
    "at least one top-row column is unmarked",
    "ordinary generated samples include a lower-row cell in an unmarked column",
    "the authoritative output is freshly zeroed before marked columns are filled",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-slot canonical-profile schedule",
        "valid": "5..9",
        "doc": "exact returned grid height",
    },
    "grid_w": {
        "type": "int",
        "default": "five-slot canonical-profile schedule",
        "valid": "6..11",
        "doc": "exact returned grid width",
    },
    "n_markers": {
        "type": "int",
        "default": "five-slot canonical-profile schedule",
        "valid": "2..5",
        "doc": "exact number of distinct nonzero first-row markers",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# These are exactly the five canonical input profiles when palette cardinality
# counts the zero background.  Reusing a marker color for the erasure witness
# preserves the profile's distinct-color count.
CANONICAL_PROFILE_SCHEDULE: tuple[tuple[int, int, int], ...] = (
    (6, 8, 3),
    (7, 9, 2),
    (5, 10, 3),
    (8, 8, 2),
    (7, 11, 3),
)
LESSON_SCHEDULE_PERIOD = len(CANONICAL_PROFILE_SCHEDULE)
SCHEDULE_PROFILES = tuple(
    f"{height}x{width}-markers-{markers}"
    for height, width, markers in CANONICAL_PROFILE_SCHEDULE
)


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    band = _normalize_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(f"{label} must be an integer (not bool)")
    return band


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the named slot in the declared five-sample schedule."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    _normalize_band(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    """Use a scheduled default while keeping every public override exact."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic teaching input.

    Difficulty is accepted as a curriculum label, but all bands deliberately
    cover the same five canonical profiles.  The random degrees of freedom are
    marker columns, marker colors, and the erasure-witness position/color.
    """
    band = _validate_call(seed, sample_index, difficulty, overrides)
    scheduled_h, scheduled_w, scheduled_markers = CANONICAL_PROFILE_SCHEDULE[
        sample_index % LESSON_SCHEDULE_PERIOD
    ]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 5, 9)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 6, 11)
    marker_count = _draw_exact_int(ctx, "n_markers", scheduled_markers, 2, 5)

    # width >= 6 and marker_count <= 5 guarantee an unmarked witness column.
    layout_rng = ctx.draw_rng(f"marker_layout:{band}")
    columns = list(range(width))
    layout_rng.shuffle(columns)
    marker_columns = columns[:marker_count]
    colors = list(
        ctx.draw_distinct_colors(f"marker_colors:{band}", n=marker_count, exclude={0})
    )

    grid = full_grid(height, width, 0)
    for column, color in zip(marker_columns, colors):
        grid[0][column] = color

    unmarked_columns = [column for column in range(width) if grid[0][column] == 0]
    witness_rng = ctx.draw_rng(f"erasure_witness:{band}")
    witness_row = witness_rng.randrange(1, height)
    witness_column = witness_rng.choice(unmarked_columns)
    witness_color = witness_rng.choice(colors)
    grid[witness_row][witness_column] = witness_color
    return grid


def _grid_shape_and_values(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return 0, 0, ["grid rows must be sequences"]
    if not grid[0]:
        return len(grid), 0, ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return len(grid), width, ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return len(grid), width, ["grid values must be integer ARC colors 0..9"]
    return len(grid), width, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar without consulting draw state."""
    del difficulty, meta
    height, width, errors = _grid_shape_and_values(grid)
    if errors:
        return errors

    if not 5 <= height <= 9:
        errors.append(f"grid height must be 5..9, found {height}")
    if not 6 <= width <= 11:
        errors.append(f"grid width must be 6..11, found {width}")
    if errors:
        return errors

    marker_columns = [column for column, value in enumerate(grid[0]) if value != 0]
    marker_colors = [grid[0][column] for column in marker_columns]
    if not 2 <= len(marker_columns) <= 5:
        errors.append(
            f"top row must contain 2..5 nonzero markers, found {len(marker_columns)}"
        )
    if len(marker_colors) != len(set(marker_colors)):
        errors.append("top-row marker colors must be distinct")
    if len(marker_columns) == width:
        errors.append("at least one top-row column must be unmarked")

    marker_color_set = set(marker_colors)
    lower_nonzero = 0
    for row in range(1, height):
        for column, value in enumerate(grid[row]):
            if value == 0:
                continue
            lower_nonzero += 1
            if grid[0][column] != 0:
                errors.append(
                    f"lower-row content may only occur in unmarked columns; found {(row, column)}"
                )
            if value not in marker_color_set:
                errors.append(
                    f"lower-row color {value} at {(row, column)} is not a marker color"
                )
            if len(errors) >= 8:
                return errors
    if lower_nonzero > 3:
        errors.append(f"at most three lower-row witness cells are allowed, found {lower_nonzero}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The accepted grammar is the measured canonical manifold plus witnesses."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover all public axes directly from pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generated grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": sum(value != 0 for value in grid[0]),
    }


def authoritative_output(grid):
    """Apply the selected fresh-grid column-fill rule."""
    height = len(grid)
    width = len(grid[0])
    out = full_grid(height, width, 0)
    for column, color in enumerate(grid[0]):
        if color != 0:
            for row in range(height):
                out[row][column] = color
    return out


def _preserve_lower_cells(grid):
    """Canonical-fitting shortcut: copy input, then fill marked columns."""
    out = [list(row) for row in grid]
    for column, color in enumerate(grid[0]):
        if color != 0:
            for row in range(len(grid)):
                out[row][column] = color
    return out


def _has_erased_unmarked_cell(grid) -> bool:
    """True when fresh-grid and preserve-input rules disagree."""
    height, width, errors = _grid_shape_and_values(grid)
    if errors or height < 2:
        return False
    return any(
        grid[row][column] != 0 and grid[0][column] == 0
        for row in range(1, height)
        for column in range(width)
    )


SEMANTIC_WITNESSES = {"erased_unmarked_cell": _has_erased_unmarked_cell}
SEMANTIC_RIVALS = {"preserve_lower_cells": _preserve_lower_cells}
# Keep the exact same callable object in all three registries so tools can
# compare declarations by identity as well as behavior.
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
WITNESS_RIVALS = {"erased_unmarked_cell": ["preserve_lower_cells"]}


def lesson_identifiable(demos, query) -> list[str]:
    """Verify outputs and require demos to refute any query-relevant rival."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    rival_survives = True
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        grammar_errors = self_check(grid)
        if grammar_errors:
            errors.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = authoritative_output(grid)
        if demo["output"] != expected:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        if _preserve_lower_cells(grid) != expected:
            rival_survives = False

    query_grid = query["input"]
    if self_check(query_grid):
        errors.append("query input is outside the teaching grammar")
        return errors
    expected_query = authoritative_output(query_grid)
    if "output" in query and query["output"] != expected_query:
        errors.append("query output disagrees with the selected rule")
    if rival_survives and _preserve_lower_cells(query_grid) != expected_query:
        errors.append("demonstrations leave rival rule alive: preserve_lower_cells")
    return errors
