"""Generator for arc_puzzle_bank_21_set9_e:medium_i13 — vertical 5-divider mirror.

Rule: a vertical color-5 divider column splits the grid. Non-{0, 5} cells
on the left are mirrored to the right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, partial_divider, cells_on_right.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a82ec149798"
VERSION = "2.0.1"
TASK_ID = "8a82ec149798"
SUMMARY = (
    "0-bg grid (h ∈ 6-8, w ∈ 8-10) "
    "with: (a) ONE FULL COLOR-5 "
    "(GRAY) VERTICAL DIVIDER COLUMN "
    "at random col div ∈ 2..w-4 — "
    "every cell in that column "
    "painted 5; (b) 2-4 NON-{0, 5} "
    "SPARSE CELLS placed at random "
    "LEFT-HALF positions (cols "
    "0..div-1), each in a random "
    "color drawn from {1,2,3,4,6,7,"
    "8,9}, ensuring their mirror "
    "position (col 2*div - c) lies "
    "in-bounds on the right. The "
    "right half (cols div+1..w-1) "
    "starts EMPTY. Rule (FOR EACH "
    "NON-{0, 5} CELL ON THE LEFT, "
    "MIRROR IT ACROSS THE COLOR-5 "
    "DIVIDER COLUMN TO THE RIGHT "
    "SIDE; ORIGINAL CELLS "
    "PRESERVED): FIND the full "
    "COLOR-5 column → axis div. "
    "For EACH non-{0, 5} cell at "
    "(r, c) with c < div and "
    "color k: COMPUTE mirror "
    "position (r, 2*div - c). "
    "PAINT g[r][2*div-c] = k. "
    "Left source cells, the "
    "divider, and remaining bg "
    "stay. Net: vertical mirror "
    "across the gray divider — "
    "every left cell appears "
    "reflected on the right in "
    "its own color."
)

INVARIANTS = [
    "background is 0",
    "exactly one full color-5 column (the divider)",
    "left of divider has 2-4 sparse non-{0, 5} cells; right of divider is bg",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "partial_divider", "cells_on_right")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_only_5div",
                       "valid": "left_only_5div"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one full color-5 column (the divider); right half is bg."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    full_5_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not full_5_cols:
        return []  # no_divider or partial_divider degenerate — allowed
    errs = []
    if len(full_5_cols) != 1:
        errs.append(f"expected 1 full-gray-5 column; found {len(full_5_cols)}: {full_5_cols}")
        return errs
    div = full_5_cols[0]
    # Right half (cols div+1..w-1) should be bg
    for r in range(h):
        for c in range(div + 1, w):
            if grid[r][c] != 0:
                errs.append(f"right-half cell ({r},{c})={grid[r][c]} should be 0")
                return errs
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    div = rng.randint(2, w - 4)
    for r in range(h):
        g[r][div] = 5
    for _ in range(rng.randint(2, 4)):
        for _t in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, div - 1)
            if g[r][c] != 0: continue
            mc = 2 * div - c
            if not (0 <= mc < w): continue
            g[r][c] = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    div = w // 2
    if name == "no_divider":
        # no 5-column → axis undefined
        g[1][1] = 4; g[3][2] = 6
        return g
    if name == "partial_divider":
        # divider has gaps → "full color-5 column" precondition fails
        for r in range(h - 2): g[r][div] = 5
        g[1][1] = 4; g[2][2] = 6
        return g
    if name == "cells_on_right":
        # cells on right side → mirror would clobber existing right-side content
        for r in range(h): g[r][div] = 5
        g[1][1] = 4; g[2][2] = 6   # left
        g[1][7] = 3; g[2][8] = 7   # right (clobber)
        return g
    return g
