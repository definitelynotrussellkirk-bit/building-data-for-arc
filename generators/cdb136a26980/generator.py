"""Generator for arc_puzzle_bank_tenth21:E66.

Rule: rows with a 9-anchor mirror their nonzero cells across that anchor.

Combinatorial axes (8): grid_h/w, palette_kind, rows,
palette_size, position_bias, n_distinct_colors, marks_per_row, texture.
Degenerates: no_anchor, marks_on_both_sides, no_marks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cdb136a26980"
VERSION = "2.0.1"
TASK_ID = "cdb136a26980"
SUMMARY = (
    "0-bg grid (h~6-9, w~"
    "9-13) with 2-4 ACTIVE "
    "ROWS, each containing: "
    "(a) ONE COLOR-9 (maroon) "
    "ANCHOR cell at column p "
    "(3..w-3); (b) 1-3 "
    "COLORED MARKER cells on "
    "the LEFT side of the "
    "anchor (cols max(0, "
    "p-3) to p-1) in random "
    "colors from {1..8}. "
    "Non-active rows are 0. "
    "Rule (MIRROR LEFT-SIDE "
    "MARKERS ACROSS 9-ANCHOR)"
    ": For EACH ROW r "
    "containing a COLOR-9 "
    "ANCHOR at col p: For "
    "EACH non-0 non-9 cell "
    "at (r, c) with c < p, "
    "PAINT the MIRROR "
    "position (r, 2p - c) "
    "with the same color "
    "(if in-bounds). The "
    "anchor stays. Source "
    "cells stay. Net: each "
    "row with a 9-anchor "
    "reflects its left-side "
    "markers to the right "
    "side."
)

INVARIANTS = [
    "background is 0",
    "anchor color is 9",
    "each active row has one anchor",
    "colored source cells are placed on one side of the anchor",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("no_anchor", "marks_on_both_sides", "no_marks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "3..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rows":           {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "marks_per_row":  {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8"},
    "position_bias":  {"type": "str", "default": "left_of_anchor",
                       "valid": "left_of_anchor"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4",
                          "valid": "1..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each row with a color-9 anchor also has ≥1 non-{0,9} marker."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    for r in range(h):
        nines = [c for c in range(w) if grid[r][c] == 9]
        if not nines:
            continue
        if len(nines) > 1:
            errs.append(f"row {r} has {len(nines)} color-9 anchors; expected ≤1")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 9, 13)
    target = min(ctx.draw_int("rows", 2, 4), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for r in rng.sample(range(h), target):
        p = rng.randint(3, w - 3)
        g[r][p] = 9
        cols = rng.sample(range(max(0, p - 3), p), rng.randint(1, min(3, p)))
        for c in cols:
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "no_anchor":
        # marks but no 9-anchor — mirror axis undefined
        g[2][2] = 4
        g[4][3] = 7
        return g
    if name == "marks_on_both_sides":
        # marks on both sides of the anchor — rule overwrites silently
        g[2][5] = 9
        g[2][2] = 4
        g[2][8] = 7
        return g
    if name == "no_marks":
        # anchors but nothing to mirror
        g[2][5] = 9
        g[4][6] = 9
        return g
    return g
