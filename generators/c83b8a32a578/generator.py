"""Generator for arc_puzzle_bank_tenth21:H66 — rotate-stamp around 9-pivot.

Rule: (0, 0) holds n, the rotation count (1..4). A color-9 pivot defines
the rotation center. Other non-zero cells define a shape; the shape is
rotated k times by 90° around the pivot for k=0..n-1, painted in shape's
color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_count, no_pivot, no_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c83b8a32a578"
VERSION = "1.2.0"
TASK_ID = "c83b8a32a578"

SUMMARY = "(0,0)=rotation count + color-9 pivot + a small motif in some other color near the pivot."

INVARIANTS = [
    "background is 0",
    "(0, 0) holds an integer 1..4 (rotation count)",
    "exactly one color-9 pivot cell at the center area",
    "1-3 non-zero cells in some non-{0, 9} color near the pivot (the shape to rotate)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_count", "no_pivot", "no_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_count":        {"type": "int", "default": "rng 2..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "count_pivot_shape",
                       "valid": "count_pivot_shape"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    # rotation count covers the full 1..4 range (was hardcoded 2..4, missing the
    # n=1 'rotate once' branch); spread by difficulty.
    if difficulty == "easy":
        n = rng.randint(1, 3)
    elif difficulty == "hard":
        n = rng.randint(2, 4)
    else:
        n = rng.randint(1, 4)
    g[0][0] = n
    pr = h // 2; pc = w // 2
    g[pr][pc] = 9
    color = rng.choice([2, 3, 4, 5, 6, 7, 8])
    n_shape = rng.randint(1, 3)
    placed = 0
    for _ in range(80):
        if placed >= n_shape: break
        dr = rng.choice([-1, 0, 1, 2])
        dc = rng.choice([-1, 0, 1, 2])
        if (dr, dc) == (0, 0): continue
        r, c = pr + dr, pc + dc
        if not (0 <= r < h and 0 <= c < w): continue
        if g[r][c] != 0: continue
        g[r][c] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_count":
        # pivot + shape but no rotation count at (0,0) → undefined repetition
        g[4][4] = 9
        g[3][4] = 4; g[4][5] = 4
        return g
    if name == "no_pivot":
        # count + shape but no 9-pivot → no rotation center
        g[0][0] = 3
        g[3][3] = 4; g[3][4] = 4
        return g
    if name == "no_shape":
        # count + pivot but no shape → nothing to rotate
        g[0][0] = 3
        g[4][4] = 9
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not (h and w and 1 <= grid[0][0] <= 4):
        errs.append(f"rotation count at (0,0) must be 1..4, got {grid[0][0] if h and w else None}")
    pivots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(pivots) != 1:
        errs.append(f"expected exactly one 9 pivot, got {len(pivots)}")
    motif = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 9) and (r, c) != (0, 0)]
    if not (1 <= len(motif) <= 3):
        errs.append(f"expected 1..3 motif cells, got {len(motif)}")
    if motif and len({v for _, _, v in motif}) != 1:
        errs.append("motif cells should share one non-9 color")
    if pivots:
        pr, pc = pivots[0]
        if any(abs(r - pr) > 2 or abs(c - pc) > 2 for r, c, _ in motif):
            errs.append("motif cells should be near the pivot")
    return errs
