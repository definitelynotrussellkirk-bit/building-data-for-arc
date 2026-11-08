"""Input sampler for projecting top-row color markers down their columns.

The authoritative Racket rule is unchanged: each nonzero cell in row 0 colors
its entire output column, while unmarked columns remain background.  This file
samples lawful inputs only; semantic rival functions below are diagnostics, not
label authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c0d744296ec"
TASK_ID = GENERATOR_ID
RULE_HASH = "c508f4ec9417"
VERSION = "2.0.0"
SUMMARY = "Distinct top-row color markers project their colors down full columns."
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0",
    "grid shape is 6..12 rows by 8..14 columns",
    "the top row has 2..6 markers with distinct colors from 1..9",
    "every body cell is background",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted canonical profiles plus broad 6..12 support",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted canonical profiles plus broad 8..14 support",
        "valid": "8..14",
    },
    "markers": {
        "type": "int",
        "default": "weighted canonical profiles plus broad 2..6 support",
        "valid": "2..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# (height, width, nonzero palette size).  These are the five canonical input
# profiles.  A weighted branch anchors every difficulty band while a broad
# branch still covers the full declared domain.
_CANONICAL_PROFILES = (
    (6, 10, 3),
    (7, 9, 3),
    (7, 10, 3),
    (8, 8, 2),
    (9, 11, 3),
)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _weighted_int(ctx, name, lo, hi, *, anchor=None, favored=()):
    """Draw across the full contract while strongly weighting one profile."""
    options = list(range(lo, hi + 1))
    options.extend(favored)
    if anchor is not None:
        options.extend([anchor] * 64)
    return ctx.draw_choice(name, options)


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

    mode = ctx.draw_choice("curriculum_mode", ("canonical", "canonical", "broad"))
    profile = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    anchor_h, anchor_w, anchor_markers = profile if mode == "canonical" else (None, None, None)

    if difficulty == "easy":
        favored_h, favored_w, favored_markers = (6, 7, 8), (8, 9, 10), (2, 3)
    elif difficulty == "hard":
        favored_h, favored_w, favored_markers = (10, 11, 12), (12, 13, 14), (4, 5, 6)
    else:
        favored_h = favored_w = favored_markers = ()

    h = _weighted_int(ctx, "grid_h", 6, 12, anchor=anchor_h, favored=favored_h)
    w = _weighted_int(ctx, "grid_w", 8, 14, anchor=anchor_w, favored=favored_w)
    n_markers = _weighted_int(
        ctx, "markers", 2, 6, anchor=anchor_markers, favored=favored_markers
    )

    columns = sorted(ctx.draw_rng("marker_columns").sample(range(w), n_markers))
    colors = ctx.draw_rng("marker_colors").sample(range(1, 10), n_markers)
    grid = full_grid(h, w, 0)
    for column, color in zip(columns, colors):
        grid[0][column] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate this sampler's strict input manifold without raising."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must have a nonempty first row"]

    h = len(grid)
    w = len(grid[0])
    problems = []
    if not 6 <= h <= 12:
        problems.append(f"height {h} outside 6..12")
    if not 8 <= w <= 14:
        problems.append(f"width {w} outside 8..14")

    rectangular = True
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            problems.append(f"row {r} has invalid width")
            rectangular = False
            continue
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                problems.append(f"cell ({r},{c}) is not an ARC color 0..9")
    if not rectangular:
        return problems

    body_nonzero = [
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    if body_nonzero:
        problems.append(
            f"body rows contain {len(body_nonzero)} nonzero cell(s), expected 0"
        )

    colors = [value for value in grid[0] if value != 0]
    if not 2 <= len(colors) <= 6:
        problems.append(f"top row has {len(colors)} markers, expected 2..6")
    if len(colors) != len(set(colors)):
        problems.append("top-row marker colors must be distinct")
    return problems


def strict_canonical_like(grid):
    """Return strict-manifold diagnostics for the semantic gate."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis directly from returned pixels."""
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe invalid grid: {problems}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "markers": sum(value != 0 for value in grid[0]),
    }


def _top_row_only(grid):
    """Rival: leave the input unchanged instead of projecting markers."""
    return [list(row) for row in grid]


def _single_color_projection(grid):
    """Rival: project all marked columns using only the first marker color."""
    top = grid[0]
    first = next(value for value in top if value != 0)
    marked = [c for c, value in enumerate(top) if value != 0]
    out = full_grid(len(grid), len(top), 0)
    for r in range(len(grid)):
        for c in marked:
            out[r][c] = first
    return out


def _has_multiple_marker_colors(grid):
    return len({value for value in grid[0] if value != 0}) >= 2


SEMANTIC_WITNESSES = {"multiple_marker_colors": _has_multiple_marker_colors}
SEMANTIC_RIVALS = {
    "top_row_only": _top_row_only,
    "single_color_projection": _single_color_projection,
}
WITNESS_RIVALS = {
    "multiple_marker_colors": ["top_row_only", "single_color_projection"]
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
