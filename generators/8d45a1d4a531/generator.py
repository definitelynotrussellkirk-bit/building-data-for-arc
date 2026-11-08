"""Generator for Project the Markers to Full Crosses (8d45a1d4a531).

Every nonzero input cell is a same-color marker.  The transformation paints
that marker's complete row and complete column in the marker color; multiple
markers therefore produce the union of their full crosses.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8d45a1d4a531"
TASK_ID = "8d45a1d4a531"
VERSION = "3.0.0"
RULE_HASH = "04b45d1c8bbd"

SUMMARY = (
    "A 0-background grid contains two to four singleton markers. All markers "
    "share one nonzero color and occupy distinct rows and distinct columns. "
    "For every marker, paint its entire row and entire column in that marker "
    "color. The output is the union of all such full crosses; every other "
    "cell remains 0."
)

INVARIANTS = [
    "the background is 0 and the only nonzero cells are marker cells",
    "there are 2..4 markers, all in exactly one nonzero color",
    "marker rows are pairwise distinct and marker columns are pairwise distinct",
    "the grid has at least three unmarked rows and three unmarked columns",
    "the transformation visibly adds both horizontal and vertical cross arms",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 7..16",
        "valid": "7..16",
    },
    "markers": {
        "type": "int",
        "default": "difficulty-aware rng 2..4",
        "valid": "2..4",
    },
    "marker_color": {
        "type": "color",
        "default": "rng nonzero",
        "valid": "1..9",
    },
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "markers", "marker_color"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _analyze(grid):
    errors = []
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not all(isinstance(row, (list, tuple)) for row in grid)
        or not grid[0]
        or any(len(row) != len(grid[0]) for row in grid)
    ):
        return None, ["grid must be a non-empty rectangle"]

    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 14 or not 7 <= w <= 16:
        errors.append("grid dimensions must be within 7..14 rows and 7..16 columns")

    invalid = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append("all cells must be integer ARC colors 0..9")
        return None, errors

    markers = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    if not 2 <= len(markers) <= 4:
        errors.append(f"expected 2..4 markers, found {len(markers)}")

    colors = {value for _, _, value in markers}
    if len(colors) != 1:
        errors.append("all markers must share exactly one nonzero color")

    rows = [r for r, _, _ in markers]
    cols = [c for _, c, _ in markers]
    if len(set(rows)) != len(rows):
        errors.append("markers must occupy pairwise distinct rows")
    if len(set(cols)) != len(cols):
        errors.append("markers must occupy pairwise distinct columns")

    if markers and (h - len(set(rows)) < 3 or w - len(set(cols)) < 3):
        errors.append("at least three rows and columns must remain unmarked")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "markers": len(markers),
        "marker_color": next(iter(colors)) if len(colors) == 1 else None,
        "positions": tuple((r, c) for r, c, _ in markers),
    }
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding marker scenes."""
    _facts, errors = _analyze(grid)
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Expose exact semantic axes recoverable from a returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "markers": facts["markers"],
        "marker_color": facts["marker_color"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, nondegenerate marker-projection input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = ctx.draw_int_diff("grid_h", 7, 14)
    w = ctx.draw_int_diff("grid_w", 7, 16)
    marker_count = ctx.draw_int_diff("markers", 2, 4)
    marker_color = ctx.draw_color("marker_color", exclude={0})

    layout_rng = ctx.draw_rng("layout")
    rows = layout_rng.sample(range(h), marker_count)
    cols = layout_rng.sample(range(w), marker_count)
    layout_rng.shuffle(cols)

    grid = full_grid(h, w, 0)
    for row, col in zip(rows, cols):
        grid[row][col] = marker_color
    return grid
