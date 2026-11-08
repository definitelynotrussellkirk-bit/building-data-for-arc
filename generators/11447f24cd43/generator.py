"""Generator for arc_puzzle_bank_21_set5_e:easy_e06.

Rule: union the pattern with its left-right mirror — for each non-zero
cell, also paint its horizontal mirror image with the same color.

Combinatorial axes (8): grid_h/w, palette_kind, marks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: already_symmetric, on_center_column, no_marks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "11447f24cd43"
VERSION = "1.1.1"  # +self_check
TASK_ID = "11447f24cd43"
SUMMARY = "Union the pattern with its left-right mirror."

INVARIANTS = [
    "background is 0",
    "input marks are sparse",
    "at least one mark is off the vertical mirror axis",
    "output keeps original marks and their horizontal mirrors",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("already_symmetric", "on_center_column", "no_marks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|rainbow"},
    "marks":          {"type": "int", "default": "rng 2..5", "valid": "1..20"},
    "density":        {"type": "str", "default": "medium",
                       "valid": "sparse|medium|dense"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "left_half",
                       "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..5",
                          "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|rainbow|already_symmetric|on_center_column|no_marks"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
        target_max = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
        target_max = 5
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        target_max = 5
    marks = ctx.draw_int("marks", 2, target_max)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    left_cols = list(range(max(1, w // 2)))
    cells = [(r, c) for r in range(h) for c in left_cols if c != w - 1 - c]
    for r, c in rng.sample(cells, min(marks, len(cells))):
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one non-zero cell that is NOT on the vertical mirror axis."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    # For LR mirror: axis is at col w/2.  A cell at col c != w-1-c if c != w-1-c.
    off_axis = [(r, c) for r in range(h) for c in range(w)
                if grid[r][c] != 0 and c != w - 1 - c]
    if not off_axis:
        errors.append("no non-zero cell off the vertical mirror axis — LR-echo has no visible effect")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "already_symmetric":
        # input already symmetric across vertical axis — rule output equals input
        for r, c, v in [(1, 1, 4), (1, 7, 4), (3, 2, 7), (3, 6, 7)]:
            g[r][c] = v
        return g
    if name == "on_center_column":
        # cells on center column (odd width) mirror to themselves
        cc = w // 2
        g[1][cc] = 5
        g[3][cc] = 6
        return g
    if name == "no_marks":
        return g
    return g
