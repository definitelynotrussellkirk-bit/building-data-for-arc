"""Generator for ARC task 44e865b6a43e — rotate bar attributes separately.

The input is an orange (7) canvas containing three to five one-cell-wide,
bottom-aligned bars in every other column.  Bar colors are distinct; heights
may repeat.  The target keeps the bar columns fixed, rotates colors one place
to the right, and independently rotates heights one place to the left.

Ordinary lessons use at least three bars so the independent color/height
rotations cannot collapse into the same two-item swap.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "44e865b6a43e"
TASK_ID = "44e865b6a43e"
VERSION = "2.0.0"
RULE_HASH = "de38c98a1856"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "An orange 7..12 by (2n+1) grid contains 3..5 distinct-colored, "
    "one-cell-wide bars in alternating columns, all bottom-aligned. Heights "
    "may repeat but are not all equal. Rotate colors right and heights left."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "all cells are ARC colors 0..9 and background is color 7",
    "the grid is 7..12 rows high and has width 2*n_bars+1",
    "there are exactly 3..5 bars in columns 1,3,...,2*n_bars-1",
    "each bar is a solid, one-cell-wide, bottom-aligned run shorter than the grid",
    "bar colors are pairwise distinct and may include color 0",
    "bar heights may repeat, but at least two heights differ",
]

HEIGHT_PATTERNS = ("ascending", "descending", "mixed", "repeat")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased draw over 7..12",
        "valid": "7..12",
    },
    "n_bars": {
        "type": "int",
        "default": "difficulty-biased draw over 3..5",
        "valid": "3..5",
    },
    "height_pattern": {
        "type": "str",
        "default": "uniform keyed draw",
        "valid": "|".join(HEIGHT_PATTERNS),
    },
}


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    """Return exact scene facts and strict grammar errors."""
    facts: dict[str, Any] = {
        "grid_h": None,
        "grid_w": None,
        "n_bars": None,
        "columns": [],
        "colors": [],
        "heights": [],
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty rectangular sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid must have at least one column"]

    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return facts, ["grid must be rectangular"]

    errors: list[str] = []
    invalid_cells = sorted(
        {
            repr(value)
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        }
    )
    if invalid_cells:
        errors.append(
            "all cells must be literal ARC colors 0..9; invalid values: "
            + ", ".join(invalid_cells[:6])
        )

    height = len(grid)
    facts["grid_h"], facts["grid_w"] = height, width
    if not 7 <= height <= 12:
        errors.append(f"grid height must be in 7..12, got {height}")
    if width % 2 != 1:
        errors.append(f"grid width must be odd, got {width}")
        return facts, errors

    n_bars = (width - 1) // 2
    facts["n_bars"] = n_bars
    if not 3 <= n_bars <= 5:
        errors.append(
            f"grid width must encode 3..5 alternating bars, got {n_bars}"
        )

    expected_columns = list(range(1, width - 1, 2))
    facts["columns"] = expected_columns

    # All margin/separator columns must be pure orange background.
    for col in range(0, width, 2):
        bad_rows = [row for row in range(height) if grid[row][col] != 7]
        if bad_rows:
            errors.append(
                f"background column {col} must be all 7; non-7 at rows "
                f"{bad_rows[:6]}"
            )

    colors: list[int] = []
    heights: list[int] = []
    for col in expected_columns:
        values = [grid[row][col] for row in range(height)]
        non_bg_rows = [row for row, value in enumerate(values) if value != 7]
        if not non_bg_rows:
            errors.append(f"bar column {col} is empty")
            continue

        first = non_bg_rows[0]
        bar_color = values[first]
        expected_rows = list(range(first, height))
        if non_bg_rows != expected_rows:
            errors.append(
                f"bar column {col} must be a contiguous bottom-aligned run"
            )
        if any(values[row] != bar_color for row in non_bg_rows):
            errors.append(f"bar column {col} must use one color")
        if first == 0:
            errors.append(f"bar column {col} must be shorter than the grid")
        if any(values[row] != 7 for row in range(first)):
            errors.append(f"cells above bar column {col} must be color 7")

        colors.append(bar_color)
        heights.append(height - first)

    facts["colors"] = colors
    facts["heights"] = heights
    if len(colors) == len(expected_columns) and len(set(colors)) != len(colors):
        errors.append("bar colors must be pairwise distinct")
    if len(heights) == len(expected_columns) and len(set(heights)) < 2:
        errors.append("bar heights must not all be equal")
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full task grammar, including canonical repeated heights."""
    del difficulty, meta
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict[str, int]:
    """Recover the exact non-dimensional semantic axis from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {"n_bars": int(facts["n_bars"])}


def bar_profile(grid) -> dict[str, Any]:
    """Return the validated left-to-right bar profile for audits and tests."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_bars": facts["n_bars"],
        "columns": list(facts["columns"]),
        "colors": list(facts["colors"]),
        "heights": list(facts["heights"]),
    }


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical Racket transformation."""
    profile = bar_profile(grid)
    height = int(profile["grid_h"])
    width = int(profile["grid_w"])
    columns = profile["columns"]
    colors = profile["colors"]
    heights = profile["heights"]

    output = [[7] * width for _ in range(height)]
    output_colors = [colors[-1], *colors[:-1]]
    output_heights = [*heights[1:], heights[0]]
    for col, color, bar_height in zip(columns, output_colors, output_heights):
        for row in range(height - bar_height, height):
            output[row][col] = color
    return output


def _height_sequence(ctx, *, grid_h: int, n_bars: int, pattern: str) -> list[int]:
    """Construct four disjoint, observable height families from one base draw."""
    base = sorted(
        ctx.draw_rng("bar_heights").sample(range(1, grid_h), n_bars)
    )
    if pattern == "ascending":
        return base
    if pattern == "descending":
        return list(reversed(base))
    if pattern == "mixed":
        # n_bars >= 3, so this rotation has both a rise and a fall.
        return [*base[1:], base[0]]
    if pattern == "repeat":
        # Preserve at least two distinct heights while guaranteeing a duplicate.
        return [*base[:-1], base[0]]
    raise ValueError(f"unknown height pattern {pattern!r}")


def _validate_request(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for axis in ("grid_h", "n_bars"):
        value = overrides.get(axis)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise TypeError(f"{axis} override must be an integer")
    value = overrides.get("height_pattern")
    if value is not None and not isinstance(value, str):
        raise TypeError("height_pattern override must be a string")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_h = ctx.draw_int_diff("grid_h", 7, 12)
    n_bars = ctx.draw_int_diff("n_bars", 3, 5)
    height_pattern = ctx.draw_choice("height_pattern", HEIGHT_PATTERNS)

    grid_w = 2 * n_bars + 1
    colors = ctx.draw_distinct_colors("bar_colors", n=n_bars, exclude={7})
    heights = _height_sequence(
        ctx,
        grid_h=grid_h,
        n_bars=n_bars,
        pattern=height_pattern,
    )

    grid = [[7] * grid_w for _ in range(grid_h)]
    for col, color, bar_height in zip(
        range(1, grid_w - 1, 2), colors, heights
    ):
        for row in range(grid_h - bar_height, grid_h):
            grid[row][col] = color
    return grid
