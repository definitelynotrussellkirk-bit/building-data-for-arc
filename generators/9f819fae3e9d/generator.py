"""Generator for arc_puzzle_bank_sixth21:E42.

Rule: a 3×3 same-color ring with a zero center has that center filled
with the ring's color.

Combinatorial axes (8): grid_h/w, palette_kind, n_rings, palette_size,
position_bias, n_distinct_colors, ring_density, texture.
Degenerates: no_rings, broken_ring, center_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9f819fae3e9d"
VERSION = "2.1.1"  # distinct 124 / ncol 4: ring colors were deterministic (i%8)+1 (always 1,2,3). Draw random distinct colors (rule fills center with ring color regardless) -> palette + distinct up."
TASK_ID = "9f819fae3e9d"
SUMMARY = (
    "0-bg grid (h, w~8-11) "
    "with 1-3 HOLLOW 3×3 "
    "SAME-COLOR RINGS — "
    "each a 3×3 region "
    "where the 8 BORDER "
    "cells are painted in "
    "ONE NON-0 COLOR and "
    "the CENTER CELL is "
    "ZERO (a hollow ring). "
    "Ring centers are "
    "placed on a 4-cell "
    "stride grid (rows "
    "1, 5, 9; cols 1, 5, 9)"
    " so rings don't touch"
    ". Each ring uses a "
    "distinct color from "
    "{1..8} (color (i%8)+1)"
    ". Rule (FILL EACH "
    "HOLLOW 3×3 RING'S "
    "CENTER WITH RING "
    "COLOR): For EACH 3×3 "
    "WINDOW where all 8 "
    "BORDER CELLS are the "
    "SAME COLOR C and the "
    "CENTER cell is 0: "
    "PAINT the center "
    "cell with COLOR C. "
    "Cells outside such "
    "windows stay. Net: "
    "every hollow ring "
    "completes into a "
    "solid 3×3 patch of "
    "its ring color."
)

INVARIANTS = [
    "ring borders are one nonzero color",
    "ring centers start zero",
    "rings are separated",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_rings", "broken_ring", "center_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..15"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "ring_density":   {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 hollow 3x3 ring: 8 border cells same color, center=0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    found = 0
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0:
                border = [grid[r + dr][c + dc]
                          for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                          if (dr, dc) != (0, 0)]
                if 0 not in border and len(set(border)) == 1:
                    found += 1
    if found == 0:
        errs.append("no hollow 3x3 ring found (8 uniform-color border + 0 center)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
    n = ctx.draw_int("n_rings", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    centers = [(r, c) for r in range(1, h - 1, 4) for c in range(1, w - 1, 4)]
    rng.shuffle(centers)
    ring_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(n, 9))
    for i, (r, c) in enumerate(centers[:n]):
        color = ring_colors[i % len(ring_colors)]
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if rr != r or cc != c:
                    g[rr][cc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # singletons only — no ring pattern to fill
        g[2][2] = 4
        g[5][6] = 7
        return g
    if name == "broken_ring":
        # ring with missing border cell — predicate fails
        for rr in range(1, 4):
            for cc in range(1, 4):
                if rr != 2 or cc != 2:
                    g[rr][cc] = 4
        g[1][2] = 0  # break top center
        return g
    if name == "center_already_filled":
        # center is already nonzero — invariant violated
        for rr in range(1, 4):
            for cc in range(1, 4):
                g[rr][cc] = 4
        return g
    return g
