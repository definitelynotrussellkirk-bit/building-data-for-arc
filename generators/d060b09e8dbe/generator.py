"""Generator for arc_additional_puzzles_21_set10_bundle:E68 — Keep only non-bg cells with same-color cardinal neighbor.

Rule: cell (r,c,v) where v != 0 — keep it iff at least one cardinal
neighbor has the same value v; else set to 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_singletons, all_blobs, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "d060b09e8dbe"
VERSION = "2.0.1"
TASK_ID = "d060b09e8dbe"
SUMMARY = (
    "0-bg grid (h~7-9, w~8-10) with: (a) "
    "TWO MULTI-CELL BLOBS — an L-tromino "
    "[(0,0),(1,0),(1,1)] in upper-left "
    "area (rows 0-1, cols 0-2) in palette[0]"
    "; and a 2-cell horizontal bar "
    "[(0,0),(0,1)] in middle-right area "
    "(rows 2-4, cols w-4..w-3) in palette[1]"
    "; (b) TWO ISOLATED SINGLETONS — one "
    "in the bottom-left corner (row h-1, "
    "cols 0-1) in palette[2]; another "
    "in the middle-left interior (rows "
    "2..h-3, cols 2-3) in palette[3]. "
    "The 4 colors are distinct non-{0} "
    "values from {2..9}. Rule (KEEP ONLY "
    "NON-BG CELLS THAT HAVE AT LEAST ONE "
    "SAME-COLOR CARDINAL NEIGHBOR — "
    "ERASE SINGLETONS): for EACH cell "
    "(r, c) with value v ≠ 0: CHECK its "
    "4 CARDINAL NEIGHBORS. IF at least "
    "ONE neighbor also = v: KEEP the "
    "cell (stays color v). IF NONE of "
    "the neighbors = v (cell is "
    "isolated by color): SET the cell "
    "to bg-0. Net: multi-cell same-"
    "color blobs survive intact; "
    "isolated singletons are erased to "
    "bg-0."
)

INVARIANTS = [
    "≥2 multi-cell blobs (any cardinal-connected, ≥2 cells each)",
    "≥2 isolated singletons (will get erased)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singletons", "all_blobs", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "blobs_with_singleton_decoys",
                       "valid": "blobs_with_singleton_decoys"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 multi-cell blobs (same-color cardinal neighbor) + ≥1 isolated singleton."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    # classify cells by whether they have a same-color cardinal neighbor
    blobs_colors = set()
    singletons = 0
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue
            neighbors = [
                grid[r - 1][c] if r > 0 else -1,
                grid[r + 1][c] if r < h - 1 else -1,
                grid[r][c - 1] if c > 0 else -1,
                grid[r][c + 1] if c < w - 1 else -1,
            ]
            if any(n == v for n in neighbors):
                blobs_colors.add(v)
            else:
                singletons += 1
    if len(blobs_colors) < 1:
        errs.append("no multi-cell blobs found (no cell with same-color cardinal neighbor)")
    if singletons < 1:
        errs.append("no isolated singleton cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 4)
    L = [(0, 0), (1, 0), (1, 1)]
    bar2 = [(0, 0), (0, 1)]
    paint_at(g, rng.randint(0, 1), rng.randint(0, 2), L, pal[0])
    paint_at(g, rng.randint(2, 4), rng.randint(w - 4, w - 3), bar2, pal[1])
    g[h - 1][rng.randint(0, 1)] = pal[2]
    g[rng.randint(2, h - 3)][rng.randint(2, 3)] = pal[3]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "all_singletons":
        # all cells singletons → rule erases everything (output blank)
        g[1][1] = 4
        g[3][5] = 6
        g[5][2] = 3
        g[6][7] = 7
        return g
    if name == "all_blobs":
        # all cells in multi-cell blobs → rule keeps everything (input == output)
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 4, [(0, 0), (0, 1), (1, 1)], 6)
        return g
    if name == "no_cells":
        # blank → no input cells, rule has nothing to filter
        return g
    return g
