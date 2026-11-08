"""Three equally spaced collinear dots define concentric square outlines.

The middle dot is the center; the Chebyshev distance to either endpoint is
ring spacing. The unchanged canonical Racket rule draws every ring,
including the center and outlines clipped by the grid edges.

Numeric overrides are exact integers. Dimensions span 10..30, spacing spans
2..6 where all three dots fit, and the dot color spans 1..9. Unsupported
legacy decorative/degenerate controls fail explicitly instead of being ignored.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d1cffd62646"
VERSION = "1.2.0"
TASK_ID = "1d1cffd62646"
SUMMARY = "Three collinear dots define the center and spacing of concentric square outlines."

INVARIANTS = [
    "rectangular grid with dimensions 10..30 and exact integer colors 0..9",
    "background is 0",
    "exactly three non-bg cells of the same color",
    "dots are collinear and equally spaced; the middle dot is the center",
    "step is the Chebyshev distance between adjacent dots and lies in 2..6",
]

ORIENTATIONS = {
    "vertical": (1, 0),
    "horizontal": (0, 1),
    "diag_down": (1, 1),
    "diag_up": (1, -1),
}

AXES = {
    "grid_h": {"type": "int", "default": "rng 14..24 (difficulty-dependent)",
               "valid": "10..30"},
    "grid_w": {"type": "int", "default": "rng 14..24 (difficulty-dependent)",
               "valid": "10..30"},
    "step": {"type": "int", "default": "rng 2..6 where three dots fit", "valid": "2..6"},
    "dot_color": {"type": "color", "default": "rng 1..9", "valid": "1..9"},
    "orientation": {"type": "str", "default": "rng among fitting directions",
                    "valid": "|".join(ORIENTATIONS)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic three-dot input; reject impossible overrides.

    Explicit dimensions use the full valid range regardless of difficulty.
    A requested spacing restricts unpinned dimensions and orientation choices
    so valid requests cannot fail merely because an incompatible value was drawn.
    As in GenCtx, None means that an axis is left unpinned.
    """
    unknown = set(overrides) - AXES.keys()
    if unknown:
        raise ValueError(f"unsupported overrides: {', '.join(sorted(unknown))}")
    for name, lo, hi in (("grid_h", 10, 30), ("grid_w", 10, 30),
                         ("step", 2, 6), ("dot_color", 1, 9)):
        value = overrides.get(name)
        if value is not None:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer (not bool)")
            if not lo <= value <= hi:
                raise ValueError(f"{name} must lie in {lo}..{hi}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    lo, hi = {"easy": (10, 16), "hard": (20, 30)}.get(difficulty, (14, 24))
    requested_step = overrides.get("step") or 2
    lo = max(lo, 2 * requested_step + 1)
    h_bounds = (10, 30) if overrides.get("grid_h") is not None else (lo, hi)
    w_bounds = (10, 30) if overrides.get("grid_w") is not None else (lo, hi)
    h = ctx.draw_int_strict("grid_h", *h_bounds)
    w = ctx.draw_int_strict("grid_w", *w_bounds)
    fitting = [name for name, (dr, dc) in ORIENTATIONS.items()
               if 2 * requested_step * abs(dr) < h
               and 2 * requested_step * abs(dc) < w]
    if not fitting:
        raise ValueError("requested step does not fit three collinear dots in this grid")
    orientation = ctx.draw_choice("orientation", fitting)
    dr, dc = ORIENTATIONS[orientation]
    max_step = min(6, (h - 1) // 2 if dr else 6, (w - 1) // 2 if dc else 6)
    step = ctx.draw_int_strict("step", 2, max_step)
    color = ctx.draw_color_strict("dot_color", exclude={0})
    cr = ctx.draw_int_strict("center_r", step * abs(dr), h - 1 - step * abs(dr))
    cc = ctx.draw_int_strict("center_c", step * abs(dc), w - 1 - step * abs(dc))
    grid = full_grid(h, w, 0)
    for sign in (-1, 0, 1):
        grid[cr + sign * step * dr][cc + sign * step * dc] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the three-dot input contract without trusting caller metadata."""
    if type(grid) is not list or not 10 <= len(grid) <= 30:
        return ["grid must be a list with 10..30 rows"]
    if type(grid[0]) is not list or not 10 <= len(grid[0]) <= 30:
        return ["grid rows must be lists with 10..30 columns"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid cells must be exact integer colors 0..9"]
    dots = [(r, c, color) for r, row in enumerate(grid)
            for c, color in enumerate(row) if color != 0]
    if len(dots) != 3:
        return [f"expected exactly 3 non-bg cells, found {len(dots)}"]
    if len({dot[2] for dot in dots}) != 1:
        return ["the 3 non-bg cells must have the same color"]
    first, center, last = dots
    delta = (center[0] - first[0], center[1] - first[1])
    if delta != (last[0] - center[0], last[1] - center[1]):
        return ["the 3 dots must be collinear and equally spaced"]
    if not 2 <= max(abs(delta[0]), abs(delta[1])) <= 6:
        return ["adjacent dots must have Chebyshev spacing in 2..6"]
    return []
