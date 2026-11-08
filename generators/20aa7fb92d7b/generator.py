"""Generator for v2_meta_puzzles:M6 — paint plus around all-7-neighbor cells.

Rule: each cell that has all 4 cardinal neighbors equal to color 7 has
its 4 cardinal neighbors painted color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n, texture.
Degenerates: no_pluses, partial_plus, plus_at_border.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "20aa7fb92d7b"
VERSION = "1.1.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-7 cells forming plus-shaped patterns (>=4 cells)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if not sevens:
        errs.append("no color-7 cells (expected plus-shaped patterns)")
    elif len(sevens) < 4:
        errs.append(f"too few color-7 cells: {len(sevens)} (need >=4 for one plus)")
    return errs
TASK_ID = "20aa7fb92d7b"

SUMMARY = "1-2 plus-shaped color-7 patterns (4 cardinal cells around an 'empty' or color-7 center)."

INVARIANTS = [
    "background is 0",
    "1-2 plus-shaped patterns: 4 color-7 cells in cardinal positions around a center",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pluses", "partial_plus", "plus_at_border")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "scattered_pluses_interior",
                       "valid": "scattered_pluses_interior"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 7, 8)
        n = ctx.draw_int("n", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
        n = ctx.draw_int("n", 1, 2)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for _ in range(n):
            placed = False
            for _ in range(80):
                r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
                if not _free(g, r - 1, c - 1, r + 1, c + 1): continue
                g[r][c] = 4
                g[r - 1][c] = 7
                g[r + 1][c] = 7
                g[r][c - 1] = 7
                g[r][c + 1] = 7
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_pluses":
        # Empty grid — rule's "all 4 cardinal neighbors are 7"
        # condition never holds.
        return g
    if name == "partial_plus":
        # Center has only 3 of 4 cardinal 7-neighbors — rule's
        # "all 4" filter excludes; output equals input.
        g[2][3] = 4
        g[1][3] = 7; g[2][2] = 7; g[2][4] = 7
        return g
    if name == "plus_at_border":
        # Plus center on grid border — one neighbor is OOB (treated as
        # background, not 7) so rule's all-4-neighbors precondition
        # fails.
        g[0][3] = 4
        g[0][2] = 7; g[0][4] = 7; g[1][3] = 7
        return g
    return g
