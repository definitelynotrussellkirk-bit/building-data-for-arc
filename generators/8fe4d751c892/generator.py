"""Generator for arc_additional_puzzle_bank_volume6:E42 — red singletons grow blue cardinal halos.

Rule: red singleton cells grow blue cardinal halos into empty neighbors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_singletons,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_singletons, singletons_at_corner, multi_cell_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8fe4d751c892"
VERSION = "1.1.1"
TASK_ID = "8fe4d751c892"
SUMMARY = "Red singleton cells grow blue cardinal halos into empty neighbors."

INVARIANTS = [
    "background is 0",
    "target red components are singleton cells",
    "each singleton has empty cardinal neighbors when in bounds",
    "singletons are separated so halos do not collide",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_singletons", "singletons_at_corner", "multi_cell_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_singletons":   {"type": "int", "default": "rng 2..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_red_singletons",
                       "valid": "spaced_red_singletons"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_singletons|singletons_at_corner|multi_cell_blobs"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 red (color-2) singleton cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_singletons", "singletons_at_corner", "multi_cell_blobs"):
        return errs
    if not any(grid[r][c] == 2 for r in range(h) for c in range(w)):
        errs.append("no red (color-2) cells found")
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
        n_singletons = ctx.draw_int("n_singletons", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
        n_singletons = ctx.draw_int("n_singletons", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_singletons = ctx.draw_int("n_singletons", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    cells: list[tuple[int, int]] = []
    for _ in range(220):
        if len(cells) >= n_singletons:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in cells):
            continue
        g[r][c] = 2
        cells.append((r, c))
    if not cells:
        g[2][2] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_singletons":
        # blank → no halos to grow
        return g
    if name == "singletons_at_corner":
        # singletons at corner → 2 of 4 cardinal neighbors out of bounds
        g[0][0] = 2
        g[h - 1][w - 1] = 2
        return g
    if name == "multi_cell_blobs":
        # multi-cell blobs (not singletons) → "singleton" precondition fails
        g[2][2] = 2; g[2][3] = 2   # pair
        g[5][5] = 2; g[6][5] = 2   # pair
        return g
    return g
