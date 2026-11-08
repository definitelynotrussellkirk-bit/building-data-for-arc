"""Constructive generator for the row-first-color fill rule.

Each nonblank row contains one to four colored seeds.  The reference rule fills
that row with its leftmost nonzero color; blank rows remain black.  Every
advertised axis is exact and pixel-observable.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7092d9933e2d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
SUMMARY = (
    "A black rectangular grid contains several rows of colored seeds and at "
    "least one blank row.  Fill each nonblank row with its leftmost seed color; "
    "leave blank rows black."
)

PALETTES = {
    "warm": (2, 3, 8, 9),
    "cool": (1, 2, 4, 6),
    "broad": (1, 3, 6, 9),
    "primary": (1, 2, 4, 8),
}
PALETTE_KINDS = tuple(PALETTES)
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 6..12", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 7..14", "valid": "7..14"},
    "palette_kind": {"type": "str", "default": "uniform", "valid": "|".join(PALETTE_KINDS)},
    "active_rows": {"type": "int", "default": "difficulty-weighted 2..5", "valid": "2..5"},
    "seeds_per_row": {"type": "int", "default": "difficulty-weighted 1..4", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "the grid is rectangular with background 0",
    "between two and five rows contain colored seeds",
    "at least one row is blank",
    "each active row contains one to four seeds",
]


def _strict_int_override(overrides, name):
    if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
        raise TypeError(f"{name} override must be an exact integer (not bool)")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name in ("grid_h", "grid_w", "active_rows", "seeds_per_row"):
        _strict_int_override(overrides, name)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 6, 12)
    w = ctx.draw_int_diff("grid_w", 7, 14)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    active_n = ctx.draw_int_diff("active_rows", 2, 5)
    seeds_n = ctx.draw_int_diff("seeds_per_row", 1, 4)
    if active_n >= h:
        raise ValueError("active_rows must leave at least one blank row")
    if seeds_n > w:
        raise ValueError("seeds_per_row cannot exceed grid width")

    layout_rng = ctx.draw_rng("active-row-layout")
    active = sorted(layout_rng.sample(range(h), active_n))
    palette = PALETTES[palette_kind]
    color_offset = ctx.draw_rng("row-color-offset").randrange(len(palette))
    grid = full_grid(h, w, 0)
    for index, row in enumerate(active):
        rng = ctx.draw_rng(f"row-{row}-seeds")
        cols = sorted(rng.sample(range(w), seeds_n))
        first_color = palette[(color_offset + index) % len(palette)]
        grid[row][cols[0]] = first_color
        for j, col in enumerate(cols[1:], 1):
            grid[row][col] = palette[(color_offset + index + j) % len(palette)]
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["expected row sequences"]
    width = len(grid[0]) if grid else 0
    if not width or any(len(row) != width for row in grid):
        return ["expected a nonempty rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer ARC colors 0..9"]
    active = [row for row in grid if any(value != 0 for value in row)]
    errors = []
    if len(active) < 2:
        errors.append("need at least two active rows")
    if len(active) >= len(grid):
        errors.append("need at least one blank row")
    if any(not 1 <= sum(value != 0 for value in row) <= 4 for row in active):
        errors.append("each active row must contain one to four seeds")
    return errors
